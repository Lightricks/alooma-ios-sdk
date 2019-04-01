import sys
import subprocess
import select
import atexit

# download sauce connect from https://saucelabs.com/downloads/sc-4.5.2-osx.zip
SAUCE_CONNECT_PATH = '/Users/ramamar/Downloads/sc-4.5.2-osx/bin/sc'
CONNECTED_MESSAGE = "Sauce Connect is up, you may start your tests."
FINISHED_MESSAGE = "Finished! Deleting tunnel."

# Code copied from https://github.com/appium-boneyard/sample-code/blob/master/sample-code/examples/python/sauce_connect.py
def set_up_tunnel():
    # Setting up Sauce Connect 4.x tunnel
    # May need to change ./sc/bin/sc depending on OS and directory structure
    p = subprocess.Popen(
        ['%s -u $SAUCE_USERNAME -k $SAUCE_ACCESS_KEY' % SAUCE_CONNECT_PATH],
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("[Sauce Connect]: Waiting for tunnel setup, this make take up to 30s")
    print("For detailed documentation on Sauce Connect please refer to " \
          "http://https://docs.saucelabs.com/reference/sauce-connect/")
    is_ready = False
    while not is_ready:
        reads = [p.stdout.fileno(), p.stderr.fileno()]
        ret = select.select(reads, [], [])

        for fd in ret[0]:
            if fd == p.stdout.fileno():
                read = p.stdout.readline()
                sys.stdout.write("[Sauce Connect]: %s\n" % read)

                if CONNECTED_MESSAGE.encode() in read:
                    print("[Sauce Connect]: Tunnel ready, running the test")
                    is_ready = True

            if fd == p.stderr.fileno():
                read = p.stderr.readline()
                sys.stderr.write("[Sauce Connect]: %s\n" % read)
                if FINISHED_MESSAGE.encode() in read:
                    p.terminate()
                    raise Exception("Sauce Connect could not start!")
            if p.poll():
                raise Exception("Sauce Connect could not start!")
    atexit.register(tear_down_tunnel, p)


def tear_down_tunnel(tunnel_process):
    print('Terminating sauce connect process')
    tunnel_process.terminate()


UPLOAD_FILE_CMD = '''\
zip -r ./{remote_filename} {local_app_path} \\
&& curl -u $SAUCE_USERNAME:$SAUCE_ACCESS_KEY \\
-X POST \\
-H 'Content-Type: application/octet-stream' \\
https://saucelabs.com/rest/v1\
/storage/$SAUCE_USERNAME/{remote_filename}?overwrite=true \\
--data-binary '@./{remote_filename}' \\
&& rm ./{remote_filename}
'''


def upload_app_file(local_app_path, remote_filename):
    cmd = UPLOAD_FILE_CMD.format(
        local_app_path=local_app_path,
        remote_filename=remote_filename
    )
    print('Running: %s' % cmd)
    p = subprocess.Popen([cmd], shell=True)
    p.wait()
    if p.returncode != 0:
        raise Exception('Failed uploading file to saucelabs')

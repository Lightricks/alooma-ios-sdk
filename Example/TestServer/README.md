# TestServer

The TestServer contains python code for testing the SampleApp, provided with the iossdk. It includes:

- app.py - a basic webserver that implements an endpoint for receiving events from the mobile sdk.
- example_app_driver.py - a helper class which drives the use of the sample app within a simulator. It relies on *appium*
- example_app_test.py - an implementation of unittest.TestCase which tests various usage scenarios of the SampleApp and the iossdk.
- requirements.txt - dependecies of the python code in this folder
- sauce_connect.py - wraps the usage of the sauce connect tool, to enable running the unit tests locally on a macbook, while the iOS simulator is run by Sauce labs.


## Environments

The code must run on OSX, as it depends on XCode for compilation and the iOS simulator for testing. It was designed to run in 3 different environments / modes:

1. On a local macbook pro, using the iOS simulator locally
2. On a local mackbook pro, using an iOS simulator provided by Sauce Labs
3. On TravisCI, upon every commit to the repo, with iOS Simulator provided by Sauce Labs

Note, when using the Sauce Labs iOS Simulator, a tunnel needs to be open in order to allow the Simulator on Sauce Labs to access the Test Webserver.
  - When running in mode #2, the sauce connect tunnel is setup by the example_app_driver, while relying on help functions in sauce_connect.py
  - When running in mode #3, sauce connect tunnel is setup as a Travis addon (see .travis.yml for details)

To run in mode 2, you will need to export the following environment variables:
SAUCE_USERNAME, SAUCE_ACCESS_KEY

When running in mode 3, Travis CI sets the env var 'TRAVIS', and that's how `example_app_driver.py` knows whether to setup the tunnel manually or not.


## Usage

### Running tests locally

1. Start the webserver: `python3 app.py --deubg`
2. Run the unittest: `python3 -m unittest example_app_test`

### Running tests locally, using Sauce Labs iOS simulator

1. Start the webserver: `python3 app.py --deubg`
2. Set proper env vars:
  - `export SAUCE_USERNAME=<your sauce labs username>`
  - `export SAUCE_ACCESS_KEY=<your sauce labs access key>`

### Testing / modifying .travis.yml

1. Make sure you have the travis cmd line tool: `brew install travis`
2. `cd` into the folder where the `.travis.yml` file resides.
3. To add en encrypted access key to the `.travis.yml`: `travis encrypt SAUCE_ACCESS_KEY="<your sauce labs access key>" --add`
4. Verify your `.travis.yml` with the following command: `travis lint .travis.yml`
5. Commit any change to the code and browse to https://travis-ci.org/Aloomaio/iossdk/requests to see how TravisCI runs.

**NOTE**: Travis & Sauce can only run 1 test in parallel. if a test fails, make sure there weren't two builds running in parallel, and if there was, retry.


## The test webserver: app.py

app.py implements the following endpoints:

- /track - used to send events to the test webserver.
- /events/[<token>/] - used to retrieve and delete events received by the webserver. If a token is provided, only events containing that token will be removed or returned. If no token is provided, all events will be removed or returned.
- /kill - cleanly shutdown the server. used mainly when run in background by TravisCI

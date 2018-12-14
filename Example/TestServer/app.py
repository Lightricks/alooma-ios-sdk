import flask
import json
import argparse
import base64
import sqlite3


TEST_DB = 'example_app_test_db.db'
TEST_DB_SCHEMA = '''\
create table if not exists events (
  _id integer primary key autoincrement,
  date_created datetime default current_timestamp,
  token varchar,
  data blob
);'''
INSERT_EVENT_QUERY = 'insert into events (token, data) ' \
                     'values (\'{token}\', \'{data}\');'
GET_EVENTS_QUERY = 'select _id, date_created, token, data from events;'
GET_EVENTS_BY_TOKEN_QUERY_TPL = 'select _id, date_created, token, data ' \
                                'from events where token=\'{token}\''
COMMIT = 'commit;'
COUNT_EVENTS_QUERY = 'select count(1) from events;'
COUNT_EVENTS_BY_TOKEN_QUERY_TPL = 'select count(1) from events ' \
                                  'where token=\'{token}\''
DELETE_EVENTS_QUERY = 'delete from events;'
DELETE_EVENTS_BY_TOKEN_QUERY_TPL = 'delete from events where token=\'{token}\''


app = flask.Flask('alooma-iossdk-test-server')


@app.route('/track/', methods=['POST'])
def track_event():
    decoded_data = base64.decodebytes(flask.request.form['data'].encode())
    received_events = json.loads(decoded_data)
    if len(received_events) > 0:
        cursor = get_db().cursor()
        for idx, e in enumerate(received_events):
            data = json.dumps(e)
            token = e['properties']['token']
            event_type = e.get('event', '<<nil>>')
            app.logger.info('event idx=%d type=%s token=%s',
                            idx, event_type, token)
            cursor.execute(INSERT_EVENT_QUERY.format(token=token, data=data))
        cursor.execute(COMMIT)

    return "0", 200

@app.route('/events/', methods=['GET', 'DELETE'])
def events():
    if flask.request.method == 'GET':
        return get_events()
    elif flask.request.method == 'DELETE':
        return delete_events()


@app.route('/events/<token>', methods=['GET', 'DELETE'])
def events_by_token(token):
    if flask.request.method == 'GET':
        return get_events(token)
    elif flask.request.method == 'DELETE':
        return delete_events(token)

def get_events(token=None):
    cursor = get_db().cursor()
    if token:
        query = GET_EVENTS_BY_TOKEN_QUERY_TPL.format(token=token)
    else:
        query = GET_EVENTS_QUERY
    all_events = cursor.execute(query).fetchall()
    app.logger.info('GET EVENTS: %s', all_events)
    result = {
        'events': [
            {
                '_id': r[0],
                'timestamp': r[1],
                'token': r[2],
                'data': json.loads(r[3])
            } for r in all_events
        ]
    }
    return flask.jsonify(result)

def delete_events(token=None):
    cursor = get_db().cursor()
    if token:
        count_query = COUNT_EVENTS_BY_TOKEN_QUERY_TPL.format(token=token)
        delete_query = DELETE_EVENTS_BY_TOKEN_QUERY_TPL.format(token=token)
    else:
        count_query = COUNT_EVENTS_QUERY
        delete_query = DELETE_EVENTS_QUERY
    num_events = int(cursor.execute(count_query).fetchall()[0][0])
    cursor.execute(delete_query)
    cursor.execute(COMMIT)
    return flask.jsonify({
        'success': True,
        'token': token,
        'num_deleted_events': num_events
    })


def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(TEST_DB)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.cursor().executescript(TEST_DB_SCHEMA)
        db.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser('simple iossdk http server')
    parser.add_argument('--host', '-d', default='0.0.0.0')
    parser.add_argument('--port', '-p', default='8000')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    init_db()
    app.run(host=args.host, port=args.port, debug=args.debug)

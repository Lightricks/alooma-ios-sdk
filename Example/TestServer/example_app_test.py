import unittest
import sys
import pdb
import functools
import traceback
import random
import logging
import warnings

import requests
import yaretry
import selenium

import example_app_driver


logger = logging.getLogger(__name__)


DEFAULT_PROPERTIES = {
    '$app_release', '$app_version', '$lib_version', '$manufacturer', '$model',
    '$os', '$os_version', '$radio', '$screen_height', '$screen_width',
    'distinct_id', 'message_index', 'mp_device_model', 'mp_lib', 'sending_time',
    'session_id', 'time', 'token'
}

SUPER_PROPERTIES = {
    'super_prop_str','super_prop_float', 'super_prop_bool', 'super_prop_int',
    'super_prop_date', 'super_prop_array'
}

SAMPLE_OBJECT_KEYS = {
    'custom_array', 'custom_bool', 'custom_date', 'custom_float', 'custom_int',
    'custom_string'
}

CUSTOM_OBJECT_EVENT_TYPE = 'customEventObject'


def debug_on(*exceptions):
    if not exceptions:
        exceptions = (AssertionError, )
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                pdb.set_trace()
                info = sys.exc_info()
                traceback.print_exception(*info)
                pdb.post_mortem(info[2])
                raise
        return wrapper
    return decorator


def retry_on_driver_failure(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except selenium.common.exceptions.WebDriverException:
            self.init_app_driver()
            return fn(self, *args, **kwargs)
    return wrapper


class ExampleAppTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("ignore", ResourceWarning)
        cls.delete_received_events()
        cls.init_app_driver()

    @classmethod
    def init_app_driver(cls):
        cls.app_driver = example_app_driver.ExampleAppDriver()
        cls.app_driver.set_server('http://127.0.0.1:8000')

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app_driver.close()
        except selenium.common.exceptions.InvalidSessionIdException:
            # Session was already closed
            pass

    @retry_on_driver_failure
    def setUp(self):
        # unittest resets warnings filter on every test run
        warnings.simplefilter("ignore", ResourceWarning)
        self.test_token = 'TEST_TOKEN_%d' % random.randint(100, 999)
        self.app_driver.set_token(self.test_token)
        self.app_driver.initialize_sdk()
        self.event_type = 'EVENT_TYPE_%d' % random.randint(100, 999)
        self.app_driver.set_event_type(self.event_type)
        self.app_driver.set_tracking_function(
            example_app_driver.TrackingFunction.TRACK)

    @debug_on()
    def test_basic_event_sending(self):
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertEqual(self.event_type, received_events[0]['data']['event'])
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_basic_event_with_empty_string_type(self):
        self.app_driver.set_event_type('')
        self.app_driver.send_event()

        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertEqual('', received_events[0]['data']['event'])
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_basic_event_with_nil_type(self):
        self.app_driver.set_nil_event_type()

        self.app_driver.send_event()

        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertTrue('event' not in received_events[0]['data'])
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_track_with_properties_nil_object(self):
        self.app_driver.set_tracking_function(
            example_app_driver.TrackingFunction.TRACK_WITH_PROPERTIES)
        self.app_driver.set_nil_object()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertEqual(self.event_type, received_events[0]['data']['event'])
        self.assertEqual(DEFAULT_PROPERTIES,
                         set(received_events[0]['data']['properties']))
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_track_with_properties_sample_object(self):
        self.app_driver.set_tracking_function(
            example_app_driver.TrackingFunction.TRACK_WITH_PROPERTIES)
        self.app_driver.set_sample_object()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertEqual(self.event_type, received_events[0]['data']['event'])
        self.assertTrue(
            DEFAULT_PROPERTIES.issubset(
                set(received_events[0]['data']['properties'])))
        self.assertTrue(
            SAMPLE_OBJECT_KEYS.issubset(
                set(received_events[0]['data']['properties'])))
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_track_custom_object(self):
        self.app_driver.set_tracking_function(
            example_app_driver.TrackingFunction.TRACK_CUSTOM_OBJECT)
        self.app_driver.set_sample_object()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertEqual(CUSTOM_OBJECT_EVENT_TYPE,
                         received_events[0]['data']['event'])
        self.assertEqual(DEFAULT_PROPERTIES,
                         set(received_events[0]['data']['properties']))
        self.assertTrue(
            SAMPLE_OBJECT_KEYS.issubset(set(received_events[0]['data'])))
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_track_custom_object_with_type(self):
        self.app_driver.set_tracking_function(
            example_app_driver.TrackingFunction.TRACK_CUSTOM_OBJECT_WITH_TYPE)
        self.app_driver.set_sample_object()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertEqual(self.event_type,
                         received_events[0]['data']['event'])
        self.assertEqual(DEFAULT_PROPERTIES,
                         set(received_events[0]['data']['properties']))
        self.assertTrue(
            SAMPLE_OBJECT_KEYS.issubset(set(received_events[0]['data'])))
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_session_id(self):
        self.app_driver.send_event()
        self.app_driver.initialize_sdk()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token, 2)
        self.assertEqual(2, len(received_events))
        event_types = set(x['data']['event'] for x in received_events)
        self.assertEqual({self.event_type}, event_types)
        self.assertNotEqual(
            received_events[0]['data']['properties']['session_id'],
            received_events[1]['data']['properties']['session_id'])
        self.assertEqual(
            1,
            received_events[0]['data']['properties']['message_index'])
        self.assertEqual(
            1,
            received_events[1]['data']['properties']['message_index'])
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_message_index(self):
        self.app_driver.send_event()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token, 2)
        self.assertEqual(2, len(received_events))
        event_types = set(x['data']['event'] for x in received_events)
        self.assertEqual({self.event_type}, event_types)
        self.assertEqual(
            received_events[0]['data']['properties']['session_id'],
            received_events[1]['data']['properties']['session_id'])
        self.assertEqual(
            1,
            received_events[0]['data']['properties']['message_index'])
        self.assertEqual(
            2,
            received_events[1]['data']['properties']['message_index'])
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_event_with_duration(self):
        self.app_driver.add_duration_to_next_event()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token)
        self.assertEqual(1, len(received_events))
        self.assertTrue('$duration' in received_events[0]['data']['properties'])
        self.delete_received_events(self.test_token)

    @debug_on()
    def test_event_with_super_properties(self):
        self.app_driver.register_super_props()
        self.app_driver.send_event()
        self.app_driver.clear_all_super_props()
        self.app_driver.send_event()
        received_events = self.get_received_events(self.test_token, 2)
        self.assertEqual(2, len(received_events))
        self.assertTrue(
            SUPER_PROPERTIES.issubset(
                set(received_events[0]['data']['properties'])))
        self.assertTrue(
            SUPER_PROPERTIES.isdisjoint(
                set(received_events[1]['data']['properties'])))
        self.delete_received_events(self.test_token)

    @yaretry.decorate(yaretry.Params(timeout=60))
    def get_received_events(self, expected_token='', min_count=1):
        url = 'http://127.0.0.1:8000/events/%s' % expected_token
        res = requests.get(url).json()
        if len(res['events']) < min_count:
            raise Exception('received %d of %d events (token=%s)' % (
                len(res['events']), min_count, expected_token))
        return res['events']

    @staticmethod
    def delete_received_events(token=''):
        res = requests.delete('http://127.0.0.1:8000/events/%s' % token)
        res.raise_for_status()
        logger.info(res.json())

import os
import enum
import functools
import glob
import sys

from appium import webdriver
import selenium

try:
    IOSSDK_EXAMPLE_APP_PATH = glob.glob(
        os.path.expanduser('~/Library/Developer/Xcode/DerivedData/') +
        'SampleApp-*/Build/Products/Debug-iphonesimulator/SampleApp.app'
    ).pop()
except Exception as e:
    print('Could not find SampleApp.app: %s' % str(e))

WEBDRIVER_CAPABILITIES = {
    'platformName': 'iOS',
    'platformVersion': '12.1',
    'deviceName': 'iPhone 7',
    'browserName': '',
    'appiumVersion': '1.9.1',
    'automationName': 'XCUITest',
    'simpleIsVisibleCheck': False,
    'app': IOSSDK_EXAMPLE_APP_PATH
}

try:
    SAUCE_USERNAME = os.environ['SAUCE_USERNAME']
    SAUCE_ACCESS_KEY = os.environ['SAUCE_ACCESS_KEY']
    USING_SAUCE = True
    DRIVER_URL = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub" % (
        SAUCE_USERNAME, SAUCE_ACCESS_KEY)
    import sauce_connect
    if not os.environ.get('TRAVIS'):
        # running locally, setting up sauce connect manually
        sauce_connect.set_up_tunnel()
    sauce_connect.upload_app_file(IOSSDK_EXAMPLE_APP_PATH, 'sample_app.zip')
    WEBDRIVER_CAPABILITIES['platformVersion'] = '12.0'
    WEBDRIVER_CAPABILITIES['deviceName'] = 'iPhone 7 Simulator'
    WEBDRIVER_CAPABILITIES['app'] = 'sauce-storage:sample_app.zip'
except KeyError:
    USING_SAUCE = False
    DRIVER_URL = 'http://localhost:4723/wd/hub'

class TrackingFunction(enum.Enum):
    TRACK = 0
    TRACK_WITH_PROPERTIES = 1
    TRACK_CUSTOM_OBJECT = 2
    TRACK_CUSTOM_OBJECT_WITH_TYPE = 3


def scroll_up_wrapper(fn):
    @functools.wraps(fn)
    def scrolling_up_decorator(self, *args, **kwargs):
        try:
            element = fn(self, *args, **kwargs)
            if not element.is_displayed():
                self.scroll_up()
            return element
        except selenium.common.exceptions.NoSuchElementException:
            self.scroll_up()
            return fn(self, *args, **kwargs)
    return scrolling_up_decorator


def scroll_down_wrapper(fn):
    @functools.wraps(fn)
    def scrolling_down_decorator(self, *args, **kwargs):
        try:
            element = fn(self, *args, **kwargs)
            if not element.is_displayed():
                self.scroll_down()
            return element
        except selenium.common.exceptions.NoSuchElementException:
            self.scroll_down()
            return fn(self, *args, **kwargs)
    return scrolling_down_decorator


class ExampleAppDriver:
    def __init__(self, new_command_timeout=120):
        '''
        new_command_timeout controls how long it will take for the driver to
        close the session. when using this manually, you might want to increase
        '''
        self.capabilities = WEBDRIVER_CAPABILITIES.copy()
        self.capabilities['newCommandTimeout'] = new_command_timeout
        self.driver = webdriver.Remote(
            DRIVER_URL, self.capabilities)
        self.token_text_box = None
        self.server_text_box = None
        self.event_type_text_box = None
        self.nil_event_type_switch = None
        self.initialize_sdk_button = None
        self.send_event_button = None
        self.flush_now_button = None
        self.track_function_selector = None
        self.sample_object_selector = None
        self.register_super_props_button = None
        self.clear_all_super_props_button = None
        self.add_duration_to_next_event_button = None

    def hide_keyboard(self):
        self.driver.hide_keyboard()

    def set_token(self, token):
        self._fill_in_text_box(self.get_token_text_box(), token)

    def set_server(self, server_url):
        self._fill_in_text_box(self.get_server_text_box(), server_url)

    def set_event_type(self, event_type):
        switch = self.get_nil_event_type_switch()
        if switch.text == '0':
            switch.click()
        self._fill_in_text_box(self.get_event_type_text_box(), event_type)

    def set_nil_event_type(self):
        switch = self.get_nil_event_type_switch()
        if switch.text == '1':
            switch.click()

    def initialize_sdk(self):
        self.get_initialize_sdk_button().click()

    def send_event(self):
        self.get_send_event_button().click()
        self.get_flush_now_button().click()

    def set_tracking_function(self, tracking_function):
        self._tap_selector_option(
            self.get_track_function_selector().rect,
            4,
            tracking_function.value)

    def set_nil_object(self):
        self._set_sample_object_selector(0)

    def set_sample_object(self):
        self._set_sample_object_selector(1)

    def register_super_props(self):
        self.get_register_super_props_button().click()

    def clear_all_super_props(self):
        self.get_clear_all_super_props_button().click()

    def add_duration_to_next_event(self):
        self.get_add_duration_to_next_event_button().click()

    def scroll_down(self):
        self.hide_keyboard()
        self.driver.execute_script(
            "mobile: scroll",
            {"direction": "down"}
        )

    def scroll_up(self):
        self.hide_keyboard()
        self.driver.execute_script(
            "mobile: scroll",
            {"direction": "up"}
        )

    def _set_sample_object_selector(self, option_idx):
        self._tap_selector_option(
            self.get_sample_object_selector().rect, 2, option_idx)

    def _tap_selector_option(self, rect, num_options, option_idx):
        half_button_width = int(rect['width'] / num_options / 2)
        self.driver.tap([[
            rect['x'] + half_button_width + (
                option_idx * 2 * half_button_width
            ),
            rect['y'] + 1
        ]])

    @scroll_up_wrapper
    def get_token_text_box(self):
        if self.token_text_box is None:
            self.token_text_box = self.driver.find_element_by_accessibility_id(
                'token_text_box')
        return self.token_text_box

    @scroll_up_wrapper
    def get_server_text_box(self):
        if self.server_text_box is None:
            self.server_text_box = self.driver.find_element_by_accessibility_id(
                'server_text_box')
        return self.server_text_box

    @scroll_up_wrapper
    def get_event_type_text_box(self):
        if self.event_type_text_box is None:
            self.event_type_text_box = \
                self.driver.find_element_by_accessibility_id(
                    'event_type_text_box')
        return self.event_type_text_box

    @scroll_up_wrapper
    def get_nil_event_type_switch(self):
        if self.nil_event_type_switch is None:
            self.nil_event_type_switch = \
                self.driver.find_element_by_accessibility_id(
                    'is_event_type_nil')
        return self.nil_event_type_switch

    @scroll_up_wrapper
    def get_initialize_sdk_button(self):
        if self.initialize_sdk_button is None:
            self.initialize_sdk_button = \
                self.driver.find_element_by_accessibility_id(
                    'initialize_sdk_button')
        return self.initialize_sdk_button

    def get_send_event_button(self):
        if self.send_event_button is None:
            self.send_event_button = \
                self.driver.find_element_by_accessibility_id(
                    'send_event_button')
        return self.send_event_button

    def get_flush_now_button(self):
        if self.flush_now_button is None:
            self.flush_now_button = \
                self.driver.find_element_by_accessibility_id(
                    'flush_now_button')
        return self.flush_now_button

    @scroll_up_wrapper
    def get_track_function_selector(self):
        if self.track_function_selector is None:
            self.track_function_selector = \
                self.driver.find_element_by_accessibility_id(
                    'track_method_selector')
        return self.track_function_selector

    def get_sample_object_selector(self):
        if self.sample_object_selector is None:
            self.sample_object_selector = \
                self.driver.find_element_by_accessibility_id(
                    'is_sample_object_included')
        return self.sample_object_selector

    @scroll_down_wrapper
    def get_register_super_props_button(self):
        if self.register_super_props_button is None:
            self.register_super_props_button = \
                self.driver.find_element_by_accessibility_id(
                    'register_super_props_button')
        return self.register_super_props_button

    @scroll_down_wrapper
    def get_clear_all_super_props_button(self):
        if self.clear_all_super_props_button is None:
            self.clear_all_super_props_button = \
                self.driver.find_element_by_accessibility_id(
                    'clear_all_super_props')
        return self.clear_all_super_props_button

    @scroll_down_wrapper
    def get_add_duration_to_next_event_button(self):
        if self.add_duration_to_next_event_button is None:
            self.add_duration_to_next_event_button = \
                self.driver.find_element_by_accessibility_id(
                    'add_duration_to_next_event')
        return self.add_duration_to_next_event_button

    def _fill_in_text_box(self, textbox, content):
        textbox.click()
        textbox.clear()
        textbox.send_keys(content)
        self.hide_keyboard()

    def close(self):
        self.driver.quit()

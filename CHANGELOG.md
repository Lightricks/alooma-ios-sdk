## v0.1.4

- *Increased reliability and session tracking*: We've added two values to help track the uniqueness of events, as well as their order within a session of usage.
  - `"session_id"` property added to all events. Its value is assigned to a UUID when the Alooma object is instantiated, and is kept constant.
  - `"message_index"` property added to all events. Its value is assigned to 0 when the Alooma object is instantiated, and it is incremented with every event.
- *Easier integration with AppExtension*: An AppExtension is the runtime environment of push notifications as well as WatchOS apps. Previously, to include the Alooma library in AppExtension projects, one had to import a different CocoaPod (_Alooma-iOS-AppExtension_), which used preprocessor directives to exclude some parts of the code. In this version, the detection of the AppExtension runtime is performed dynamically, during the Alooma object instantiation.
- *bugfix: Accessing UIApplication applicationState from a background thread*: The library will now keep track of its background/foreground state by saving the state when `applicationDidBecomeActive` and `applicationDidEnterBackground` are called.
- *Improved SampleApp and New Automatic Tests*: some minor improvements were made to the SampleApp, and automatic tests were added using Appium, Python, Selenium, TravisCI, and Sauce Labs 

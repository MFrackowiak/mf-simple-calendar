# mf-simple-calendar

## Design assumptions

* Only backend is implemented with appropriate API.
* Date/time is saved in database in utc timezone. Timezone info is saved additionally.
* Calendar colors are from CSS3/SVG named colors.
* All-day events span the whole day in their timezone; the day of the event is displayed differently if time difference is higher than 12 hours.
* Event owner (creator) is automatically invited to his/her event.
* Event owner can't edit his/her invite, can only perform general event edits.
* There can be only one event owner.
* Only users with edit-permission on event calendar can send invitations.
* Only users with read-permission on event calendar or invited to event can see list of its guests.
* Only calendar owner can share it further.
* Assumed simplification - app only operate with integer utc timezone offsets.

## App design

App is a traditional three-layered application.

1. Data access - `DatabaseManager` utilizing SQLAlchemy to connect with MySQL database. This layer implements some basic logic as SQL constraints (uniqueness of shares, invites or usernames).
2. Application logic - `Calendar` implementing most of the app logic - like user privileges to perform certain actions or checking correct format of received data.
3. Presentation - REST-like API based on Flask framework, which only checks completness of received requests.

To simplify conversion of data to JSON format, python dictionaries are widely used format returned by methods.

## API

API utilizes JSON format to send receive data. Each response contains at least flag if given operation was successful - `{'success': True}` if it was, or if not, together with error information `{'success': False, 'err': <int:error_code>, 'message': <str:short error description>}`. If successful operation should also return data, it is returned with key and value (int, JSON object list) suitable for the operation.
All dates are returned in format `%Y-%m-%d %H:%M:%S %z` (as in Python datetime). For normal events (not all-day) dates are returned in both event timezone and user timezone.

### Error codes

* 1 - Errors caused by user input
* 2 - Database errors
* 3 - Privileges errors
* 4 - Malformed requests, bad format or missing data
* 5 - Server errors
* 9 - Unknown error cause

### Attendance status mapping

* 0 - unknown
* 1 - not attending
* 2 - don't know
* 3 - attending

### Interface

*Note: `None` in returned means that given method returns only `success` flag.*

* `/user`

   **Method**: PUT
   **Data**: `{'username': <str>, 'password': <str>, 'timezone': <int>}`
   **Returned**: `{'user_id': <int>}`
   Creates new user with given data.
* `/users/<str:like>`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'users': [{'user_id': <int>, 'username': <str>}, ...]}`
   Gets users with names similiar to given `like` string.
* `/auth`
   **Method**: POST
   **Data**: `{'username': <str>, 'password': <str>}`
   **Returned**: `{'auth': <bool>}`
   Creates session for existing user.
* `/logout`
   **Method**: PUT
   **Data**: `None`
   **Returned**: `None`
   End current user session.
* `/calendar`
   **Method**: PUT
   **Data**: `{'calendar_name': <str>, 'calendar_color': <str>}`
   **Returned**: `{'calendar_id': <int>}`
   Creates new calendar.
* `/calendar/<int:calendar_id>`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'events': [{'all_day_event': <bool>, 'event_name': <str>, 'event_timezone': <int>, 'event_id': <int>, 'end_time': <str>, 'start_time': <str>, 'event_description': <str>, 'user_timezone': <int>, 'user_end_time': <str>, 'user_start_time': <str>}, ...]}`
   Returns all events from given calendar.
   **Method**: POST
   **Data**: `{'calendar_name': <str>, 'calendar_color': <str>}`
   **Returned**: `None`
   Edits calendar.
   **Method**: DELETE
   **Data**: `None`
   **Returned**: `None`
   Deletes calendar.
* `/calendar/<int:calendar_id>/share`
   **Method**: PUT
   **Data**: `{'user_id': <int>, 'write_permission': <bool>}`
   **Returned**: `{'share_id': <int>}`
   Shares calendar with given user at given permission level.
* `/calendars`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'calendars': {'my_calendars': [{'calendar_name': <str>, 'calendar_color': <str>, 'calendar_id': <int>}, ...], 'shared_with_me' : [{'owner': <str>, 'calendar_id': <int>, 'calendar_name': <str>, 'calendar_color': <str>, 'write_permission': <bool>}}, ...]}}`
   Returns all calendars owned or shared with given user.
* `/shares`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'shares': [{'share_id': <int>, 'calendar_name': <str>, 'calendar_color': <str>, 'write_permission': <bool>, 'shared_with': <str>}, ...]}`
   Returns all shares of owned calendars with different users.
* `/share/<int:share_id>`
   **Method**: POST
   **Data**: `{'write_permission': <bool>}`
   **Returned**: `None`
   Edits write permission of given share.
   **Method**: DELETE
   **Data**: `None`
   **Returned**: `None`
   Deletes sharing calendar with other user.
* `/calendar/<int:calendar_id>/event`
   **Method**: PUT
   **Data**: `{'all_day_event': <bool>, 'event_name': <str>, 'event_timezone': <int>, 'event_id': <int>, 'end_time': <str>, 'start_time': <str>, 'event_description': <str>}`
   **Returned**: `{'user_id': <int>}`
   Creates new event. `start_time` and `end_time` can be either in format `%Y-%m-%d %H:%M:%S %z` with `event_timezone` omitted or `null` or in format `%Y-%m-%d %H:%M:%S`.
* `/event/<int:event_id>`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'event': {'all_day_event': <bool>, 'event_name': <str>, 'event_timezone': <int>, 'event_id': <int>, 'end_time': <str>, 'start_time': <str>, 'event_description': <str>, 'user_timezone': <int>, 'user_end_time': <str>, 'user_start_time': <str>}}`
   Return given event data.
   **Method**: POST
   **Data**: `{'all_day_event': <bool>, 'event_name': <str>, 'event_timezone': <int>, 'event_id': <int>, 'end_time': <str>, 'start_time': <str>, 'event_description': <str>}`
   **Returned**: `None`
   Edits given event.
   **Method**: DELETE
   **Data**: `{'username': <str>, 'password': <str>, 'timezone': <int>}`
   **Returned**: `{'user_id': <int>}`
   Deletes given event.
* `/event/<int:event_id>/invite`
   **Method**: PUT
   **Data**: `{'user_id': <int>}`
   **Returned**: `None`
   Creates event for given user for event.
* `/event/<int:event_id>/guests`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'guests': {'no': [<str:username>, ...], 'maybe': [<str:username>, ...], 'unknown': [<str:username>, ...], 'yes': [<str:username>, ...]}}`
   Returns guest list for given event.
* `/invites(/<int:archive>)?`
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'invites': [{'user_timezone': <int>, 'user_end_time': <str>, 'event_timezone': <int>, 'end_time': <str>, 'is_owner': <bool>, 'start_time': <str>, 'all_day_event': <bool>, 'description': <str>, 'attendance': <int>, 'event_id': <int>, 'user_start_time': <str>, 'event_name': <str>, 'invite_id': <int>}, ...]}`
   Returns invites for given user. At default returns only invites for events that are not yet finished, with `archive == 0` returns only past, finished events.
* `/invite/<int:invite_id>`
   **Method**: POST
   **Data**: `{'all_day_event': <bool>, 'event_name': <str>, 'event_timezone': <int>, 'event_id': <int>, 'end_time': <str>, 'start_time': <str>, 'event_description': <str>}`
   **Returned**: `None`
   Edits event data of given invite. Unchanged values can be set to `null`.
   **Method**: GET
   **Data**: `None`
   **Returned**: `{'user_timezone': <int>, 'user_end_time': <str>, 'event_timezone': <int>, 'end_time': <str>, 'is_owner': <bool>, 'start_time': <str>, 'all_day_event': <bool>, 'description': <str>, 'attendance': <int>, 'event_id': <int>, 'user_start_time': <str>, 'event_name': <str>, 'invite_id': <int>}`
   Returns given invite.
* `/invite/<int:invite_id>/attendance`
   **Method**: POST
   **Data**: `{'attendance': <int>}`
   **Returned**: `None`
   Changes attendance status for given invite. Attendance status cannot be changed to 'unknown'
* `/invite/<int:invite_id>/restore`
   **Method**: POST
   **Data**: `None`
   **Returned**: `None`
   Deletes any private changes in invite description for event.

## Tests

Tests performed was partially automated (using attached scripts), checking proper responses app behaviour by observing log of responses. Each layer was tested separately (`database_test.py` for `DatabseManager`, `calendar_test.py` for `Calendar` and `api_test.py` for server API) and only after previous layer was checked and (most of) bugs fixed, next layer was built.
Such approach to app testing allowed to avoid (in most cases) need to debug previous layer to find erroneous code. Some bugs were still revealed only after certain conditions were met during further testing. 

## \#TODO

As always, there are some useful features which were missed during initial design. This app could definitely use:

* Week / month / year for selecting loaded events / invites.
* Better user search mechanism.
* Possibility of sending multiple invites at once or automated invites for users who share given calendar.

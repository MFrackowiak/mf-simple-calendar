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

## App design

App is a traditional three-layered application.

1. Data access - `DatabaseManager` utilizing SQLAlchemy to connect with MySQL database. This layer implements some basic logic as SQL constraints (uniqueness of shares, invites or usernames).
2. Application logic - `Calendar` implementing most of the app logic - like user privileges to perform certain actions or checking correct format of received data.
3. Presentation - REST-like API based on Flask framework, which only checks completness of received requests.

To simplify conversion of data to JSON format, python dictionaries are widely used format returned by methods.

## API

## Tests

Tests performed was partially automated (using attached scripts), checking proper responses app behaviour by observing log of responses. Each layer was tested separately (`database_test.py` for `DatabseManager`, `calendar_test.py` for `Calendar` and `api_test.py` for server API) and only after previous layer was checked and (most of) bugs fixed, next layer was built.
Such approach to app testing allowed to avoid (in most cases) need to debug previous layer to find erroneous code. Some bugs were still revealed only after certain conditions were met during further testing. 

## \#TODO

As always, there are some useful features which were missed during initial design. This app could definitely use:

* Week / month / year for selecting loaded events / invites.
* Better user search mechanism.
* Possibility of sending multiple invites at once or automated invites for users who share given calendar.

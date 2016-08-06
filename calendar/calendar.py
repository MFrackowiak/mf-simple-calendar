import webcolors

from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from .database_manager import DatabaseManager


class Calendar:
    def __init__(self):
        self._db = DatabaseManager(False)

    def _can_read_calendar(self, user_id, calendar_id):
        return self._db.get_user_calendar_privilege(user_id, calendar_id) > 0

    def _can_edit_calendar(self, user_id, calendar_id):
        return self._db.get_user_calendar_privilege(user_id, calendar_id) > 1

    def _calendar_owner(self, user_id, calendar_id):
        return self._db.get_user_calendar_privilege(user_id, calendar_id) == 3

    def _error_dict(self, error_code, error_desc):
        return {'success': False, 'error': error_code, 'message': error_desc}

    def _success_dict(self, key, value):
        return {'success': True, key: value}

    def add_user(self, username, password, own_timezone):
        username = username.strip()
        password = password.strip()

        if not 4 <= len(username) <= 30:
            return self._error_dict(1, "Username should have between 4 and 30 characters.")

        if not 8 <= len(password) <= 30:
            return self._error_dict(1, "Password should have between 8 and 30 characters.")

        if not -11 <= own_timezone <= 12:
            return self._error_dict(1, "Timezone should be between -11 and +12, 0 is UTC.")

        try:
            return self._success_dict('user', self._db.add_user(username, password, own_timezone))
        except IntegrityError:
            return self._error_dict(1, "Username already taken.")
        except Exception:
            return self._error_dict(2, "Database connection error. Contact administrator.")

    def add_calendar(self, user_id, calendar_name, calendar_color):
        calendar_name = calendar_name.strip()
        
        pass

    def add_event(self, user_id, calendar_id, event_name, event_description, start_time, end_time, event_timezone,
                  all_day_event):
        pass

    def share_calendar(self, user_id, calendar_id, share_with_id):
        pass

    def invite_user(self, user_id, event_id, invited_id, is_owner=False):
        pass

    def edit_calendar(self, user_id, calendar_id, calendar_name, calendar_color):
        pass

    def edit_event(self, user_id, event_id, event_name, event_description, start_time, end_time, event_timezone,
                   all_day_event):
        pass

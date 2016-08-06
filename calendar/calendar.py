import webcolors

from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from .database_manager import DatabaseManager
from .var_utils import get_password_hash


class Calendar:
    def __init__(self):
        self._db = DatabaseManager(False)
        self._success = {'success': True}

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

    def authorize_user(self, username, password):
        username = username.strip()
        password = password.strip()

        try:
            user_data = self._db.get_user_data(username)
        except ValueError:
            # TODO Exception!!
            return self._error_dict(1, "Wrong username or password.")
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

        if not get_password_hash(password) == user_data['password']:
            return self._error_dict(1, "Wrong username or password.")

        return user_data

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
            return self._success_dict('user_id', self._db.add_user(username, password, own_timezone))
        except IntegrityError:
            return self._error_dict(1, "Username already taken.")
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def add_calendar(self, user_id, calendar_name, calendar_color):
        calendar_name = calendar_name.strip()

        if not 4 <= len(calendar_name) <= 30:
            return self._error_dict(1, "Calendar name should have between 4 and 30 characters.")

        try:
            webcolors.name_to_hex(calendar_color)
        except ValueError:
            return self._error_dict(1, "Unknown calendar color.")

        try:
            return self._success_dict('calendar_id', self._db.add_calendar(user_id, calendar_name, calendar_color))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def add_event(self, user_id, calendar_id, event_name, event_description, start_time, end_time, event_timezone,
                  all_day_event):
        if not self._can_edit_calendar(user_id, calendar_id):
            return self._error_dict(3, "You have no edit permissions for given calendar.")

        event_name = event_name.strip()
        event_description = event_description.strip()

        if not 4 <= len(event_name) <= 30:
            return self._error_dict(1, "Event name should have between 4 and 30 characters.")

        if len(event_description) > 200:
            return self._error_dict(1, "Event description too long, it should contain up to 200 characters.")

        # TODO how flask decode date?
        if all_day_event:
            pass
        else:
            pass

        try:
            return self._success_dict('event_id', self._db.add_event(calendar_id, event_name, event_description,
                                                                     start_time, end_time, event_timezone,
                                                                     all_day_event))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def share_calendar(self, user_id, calendar_id, share_with_id, write_permission):
        if not self._calendar_owner(user_id, calendar_id):
            return self._error_dict(3, "Only calendar owner can further share it.")

        try:
            return self._success_dict('share_id', self._db.add_share(calendar_id, share_with_id, write_permission))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def invite_user(self, user_id, event_id, invited_id, is_owner=False):
        # TODO Exception na nieistniejące ID!! (nie tylko tutaj)
        if not self._can_edit_calendar(user_id, self._db.get_calendar_id_for_event(event_id)):
            return self._error_dict(3, "Calendar edit permission is required to invite to its events.")

        try:
            return self._success_dict('invite_id', self._db.add_invite(event_id, invited_id, is_owner))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def edit_calendar(self, user_id, calendar_id, calendar_name, calendar_color):
        if not self._can_edit_calendar(user_id, calendar_id):
            return self._error_dict(3, "Calendar edit permission required to perform this action.")

        try:
            if self._db.update_calendar(calendar_id, calendar_name, calendar_color):
                return self._success
            else:
                pass
                # TODO w jakich warunkach?
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def edit_event(self, user_id, event_id, event_name, event_description, start_time, end_time, event_timezone,
                   all_day_event):
        if not self._can_edit_calendar(user_id, self._db.get_calendar_id_for_event(event_id)):
            return self._error_dict(3, "Calendar edit permission is required to edit its events.")

        pass

calendar_app = Calendar()

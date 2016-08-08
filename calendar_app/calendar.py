import webcolors

from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from .database_manager import DatabaseManager
from .var_utils import get_password_hash, set_utc


class Calendar:
    def __init__(self):
        self._db = DatabaseManager(True)
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

    def _parse_date_to_utc(self, start_time, end_time, timezone_delta):
        if timezone_delta is None:
            s = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S %z")
            e = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S %z")

            if s.tzinfo.utcoffset() != s.tzinfo.utcoffset():
                raise ValueError("Start time and end time must have same timezone.")

            timezone_delta = int(s.tzinfo.utcoffset() / 60)
        else:
            s = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone(timedelta(hours=timezone_delta)))
            e = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone(timedelta(hours=timezone_delta)))

        if timezone_delta == 0:
            return s, e, timezone_delta
        else:
            return self._convert_date_to_tz(s, e, 0) + (timezone_delta,)

    def _parse_all_day_event(self, start_time, timezone_delta):
        if timezone_delta is None:
            s = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S %z").replace(hour=0, minute=0, second=0)
            e = s + timedelta(days=1)

            timezone_delta = int(s.tzinfo.utcoffset() / 60)
        else:
            s = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").replace(hour=0, minute=0, second=0, tzinfo=timezone(
                timedelta(hours=timezone_delta)))
            e = s + timedelta(days=1)

        if timezone_delta == 0:
            return s, e, timezone_delta
        else:
            return self._convert_date_to_tz(s, e, 0) + (timezone_delta,)

    def _convert_all_day_event_date_to_tz(self, start_time, original_timezone, user_timezone):
        if start_time.tzinfo is None:
            set_utc(start_time)

        if abs(original_timezone - user_timezone) > 12:
            if original_timezone > user_timezone:
                start_time -= timedelta(days=1)
            else:
                start_time += timedelta(days=1)

        return start_time, start_time + timedelta(days=1)

    def _convert_date_to_tz(self, start_time, end_time, timezone_delta):
        if start_time.tzinfo is None:
            set_utc(start_time)

        if end_time.tzinfo is None:
            set_utc(end_time)

        return start_time.astimezone(timezone(timedelta(timezone_delta))), \
               end_time.astimezone(timezone(timedelta(timezone_delta)))

    def _event_as_user_event_timezone(self, event_dict, user_timezone):
        if event_dict['all_day_event']:
            event_dict['start_time'], event_dict['end_time'] = self._convert_all_day_event_date_to_tz(
                event_dict['start_time'], event_dict['event_timezone'], user_timezone)
        else:
            event_dict['user_start_time'], event_dict['user_end_time'] = self._convert_date_to_tz(
                event_dict['start_time'], event_dict['end_time'], user_timezone)
            event_dict['start_time'], event_dict['end_time'] = self._convert_date_to_tz(event_dict['start_time'],
                                                                                        event_dict['end_time'],
                                                                                        event_dict['event_timezone'])

        event_dict['user_timezone'] = user_timezone

        return event_dict

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
            return self._error_dict(1, "Unknown calendar_app color.")

        try:
            return self._success_dict('calendar_id', self._db.add_calendar(user_id, calendar_name, calendar_color))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def add_event(self, user_id, calendar_id, event_name, event_description, start_time, end_time, event_timezone,
                  all_day_event):
        if not self._can_edit_calendar(user_id, calendar_id):
            return self._error_dict(3, "You have no edit permissions for given calendar_app.")

        event_name = event_name.strip()
        event_description = event_description.strip()

        if not 4 <= len(event_name) <= 30:
            return self._error_dict(1, "Event name should have between 4 and 30 characters.")

        if len(event_description) > 200:
            return self._error_dict(1, "Event description too long, it should contain up to 200 characters.")

        if all_day_event:
            start_time, end_time, event_timezone = self._parse_all_day_event(start_time, event_timezone)
        else:
            start_time, end_time, event_timezone = self._parse_date_to_utc(start_time, end_time, event_timezone)

            if start_time > end_time:
                return self._error_dict(1, "Event cannot end before it started.")

        try:
            event_id = self._db.add_event(calendar_id, event_name, event_description, start_time, end_time,
                                          event_timezone, all_day_event)

            self._db.add_invite(event_id, user_id, True)

            return self._success_dict('event_id', event_id)
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def share_calendar(self, user_id, calendar_id, share_with_id, write_permission):
        if not self._calendar_owner(user_id, calendar_id):
            return self._error_dict(3, "Only calendar_app owner can further share it.")

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

        event_name = event_name.strip()
        event_description = event_description.strip()

        if not 4 <= len(event_name) <= 30:
            return self._error_dict(1, "Event name should have between 4 and 30 characters.")

        if len(event_description) > 200:
            return self._error_dict(1, "Event description too long, it should contain up to 200 characters.")

        if all_day_event:
            start_time, end_time, event_timezone = self._parse_all_day_event(start_time, event_timezone)
        else:
            start_time, end_time, event_timezone = self._parse_date_to_utc(start_time, end_time, event_timezone)

            if start_time > end_time:
                return self._error_dict(1, "Event cannot end before it started.")

        try:
            return self._success_dict('event_id', self._db.update_event(event_id, event_name, event_description,
                                                                        start_time, end_time, event_timezone,
                                                                        all_day_event))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def get_calendars(self, user_id):
        try:
            return self._success_dict('calendars', self._db.get_user_calendars(user_id))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def get_events(self, user_id, user_timezone, calendar_id):
        if not self._can_read_calendar(user_id, calendar_id):
            return self._error_dict(3, "Calendar read permission required to perform this action.")

        try:
            return self._success_dict('events', list(map(lambda e: self._event_as_user_event_timezone(e, user_timezone),
                                                         self._db.get_calendar_events(calendar_id))))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def get_event(self, user_id, user_timezone, event_id):
        if not self._can_read_calendar(user_id, self._db.get_calendar_id_for_event(event_id)):
            return self._error_dict(3, "Calendar read permission required to perform this action.")

        try:
            return self._success_dict('event', self._event_as_user_event_timezone(self._db.get_event(event_id),
                                                                                  user_timezone))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def get_invites(self, user_id, user_timezone, archive=False):
        try:
            return self._success_dict('invites', list(map(lambda e: self._event_as_user_event_timezone(e,
                                                                                                       user_timezone),
                                                          self._db.get_invites(user_id, archive),)))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def edit_invite(self, user_id, invite_id, own_name, own_description, own_start, own_end, own_timezone,
                    own_all_day_event):
        if self._db.get_invite_ownership(user_id, invite_id):
            if None in [own_name, own_description, own_start, own_end, own_timezone, own_all_day_event]:
                return self._error_dict(1, "Event owner can only perform basic event edits.")

            return self.edit_event(user_id, self._db.get_event_id_for_invite(invite_id), own_name, own_description,
                                   own_start, own_end, own_timezone, own_all_day_event)

        own_name = own_name.strip() if own_name is not None else None
        own_description = own_description.strip() if own_description is not None else None

        if own_name is not None and not 4 <= len(own_name) <= 30:
            return self._error_dict(1, "Event name should have between 4 and 30 characters.")

        if own_description is not None and len(own_description) > 200:
            return self._error_dict(1, "Event description too long, it should contain up to 200 characters.")

        if own_all_day_event:
            own_start, own_end, own_timezone = self._parse_all_day_event(own_start, own_timezone)
        else:
            own_start, own_end, own_timezone = self._parse_date_to_utc(own_start, own_end, own_timezone)

            if own_start > own_end:
                return self._error_dict(1, "Event cannot end before it started.")

        try:
            if self._db.update_invite_description(user_id, invite_id, own_name, own_description, own_start, own_end,
                                                  own_all_day_event):
                return self._success
            else:
                return self._error_dict(4, "Invite does not exist or request malformed.")
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def edit_invite_attendance(self, user_id, invite_id, attendance):
        if 1 > attendance > 3:
            return self._error_dict(1, "Attendance status unknown or not allowed.")

        try:
            if self._db.update_invite_attendance(user_id, invite_id, attendance):
                return self._success
            else:
                return self._error_dict(4, "Invite does not exist or request malformed.")
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def get_shares(self, user_id):
        try:
            return self._success_dict("shares", self._db.get_user_shares(user_id))
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def edit_share_permission(self, user_id, share_id, write_permission):
        if not self._calendar_owner(user_id, self._db.get_calendar_id_for_share(share_id)):
            return self._error_dict(3, "Calendar ownership required to perform this action.")

        try:
            if self._db.update_share(share_id, write_permission):
                return self._success
            else:
                return self._error_dict(9, "Unknown error")  # possible?
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def delete_share(self, user_id, share_id):
        if not self._calendar_owner(user_id, self._db.get_calendar_id_for_share(share_id)):
            return self._error_dict(3, "Calendar ownership required to perform this action.")

        try:
            if self._db.delete_share(share_id):
                return self._success
            else:
                return self._error_dict(9, "Unknown error")  # possible?
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def delete_event(self, user_id, event_id):
        if not self._can_edit_calendar(user_id, self._db.get_calendar_id_for_event(event_id)):
            return self._error_dict(3, "Calendar ownership required to perform this action.")

        try:
            if self._db.delete_event(event_id):
                return self._success
            else:
                return self._error_dict(9, "Unknown error")  # possible?
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")

    def delete_calendar(self, user_id, calendar_id):
        if not self._calendar_owner(user_id, calendar_id):
            return self._error_dict(3, "Calendar ownership required to perform this action.")

        try:
            if self._db.delete_calendar(calendar_id):
                return self._success
            else:
                return self._error_dict(9, "Unknown error")  # possible?
        except Exception:
            return self._error_dict(2, "Database error. Contact administrator.")


calendar_app = Calendar()

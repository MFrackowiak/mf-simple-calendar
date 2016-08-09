from sqlalchemy import create_engine, Table, Column, Integer, DateTime, String, MetaData, ForeignKey, Boolean, \
    UniqueConstraint, select, alias
from sqlalchemy.sql import and_, or_
from sqlalchemy_utils import create_database, database_exists
from datetime import datetime

from .config import server_type, server_url, db_user, db_password, database_name, debug
from .var_utils import get_password_hash, set_utc


class DatabaseManager:
    def __init__(self, create_new_if_needed=False):
        self._engine = self._get_engine()

        if not database_exists(self._engine.url):
            if create_new_if_needed:
                create_database(self._engine.url)
            else:
                raise ConnectionError("Database does not exist at given host.")

        metadata = MetaData()

        self._users = Table('users', metadata,
                            Column('user_id', Integer, primary_key=True),
                            Column('username', String(30), unique=True, nullable=False),
                            Column('password', String(64), nullable=False),
                            Column('own_timezone', Integer, nullable=False),
                            UniqueConstraint('username', name='unique_username'))

        self._calendars = Table('calendars', metadata,
                                Column('calendar_id', Integer, primary_key=True),
                                Column('owner_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'),
                                       nullable=False),
                                Column('calendar_name', String(30), nullable=False),
                                Column('calendar_color', String(25), nullable=False))

        self._events = Table('events', metadata,
                             Column('event_id', Integer, primary_key=True),
                             Column('calendar_id', Integer, ForeignKey('calendars.calendar_id', ondelete='CASCADE'),
                                    nullable=False),
                             Column('event_name', String(30), nullable=False),
                             Column('event_description', String(200), nullable=False),
                             Column('start_time', DateTime, nullable=False),
                             Column('end_time', DateTime, nullable=False),
                             Column('event_timezone', Integer, nullable=False),
                             Column('all_day_event', Boolean, nullable=False))

        self._shares = Table('shares', metadata,
                             Column('share_id', Integer, primary_key=True),
                             Column('calendar_id', Integer, ForeignKey('calendars.calendar_id', ondelete='CASCADE'),
                                    nullable=False),
                             Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                             Column('write_permission', Boolean, nullable=False),
                             UniqueConstraint('calendar_id', 'user_id', name='unique_shares'))

        self._invites = Table('invites', metadata,
                              Column('invite_id', Integer, primary_key=True),
                              Column('event_id', Integer, ForeignKey('events.event_id', ondelete='CASCADE'),
                                     nullable=False),
                              Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'),
                                     nullable=False),
                              Column('is_owner', Boolean, default=False),
                              Column('has_edited', Boolean, default=False),
                              Column('own_name', String(30), nullable=True),
                              Column('own_description', String(200), nullable=True),
                              Column('own_start_time', DateTime, nullable=True),
                              Column('own_end_time', DateTime, nullable=True),
                              Column('own_timezone', Integer, nullable=True),
                              Column('own_all_day_event', Boolean, nullable=True),
                              Column('attendance_status', Integer, default=0, nullable=False),
                              UniqueConstraint('event_id', 'user_id', name='unique_invites'))

        if create_new_if_needed:
            metadata.create_all(self._engine)

    def _get_engine(self):
        return create_engine(
            "{type}://{user}:{pswd}@{host}/{name}".format(type=server_type, user=db_user, pswd=db_password,
                                                          host=server_url, name=database_name),
            encoding='utf8', echo=debug)

    def _execute_single_insert(self, _insert):
        connection = self._engine.connect()

        result = connection.execute(_insert)

        connection.close()

        return result.inserted_primary_key[0]

    def _execute_single_update_delete(self, _query):
        connection = self._engine.connect()

        result = connection.execute(_query)

        connection.close()

        return result.rowcount == 1

    def _fetch_single_select(self, _select, mapping=None):
        connection = self._engine.connect()

        result = connection.execute(_select)

        connection.close()

        if result.rowcount < 1:
            raise ValueError("Given record does not exist in database.")

        return mapping(result.fetchone()) if mapping is not None else result.fetchone()

    def _fetch_many_select(self, _select, mapping=None):
        connection = self._engine.connect()

        result = connection.execute(_select).fetchall()

        connection.close()

        return list(map(mapping, result)) if mapping is not None else result  # 3.4!

    def add_user(self, username, password, own_timezone):
        _insert = self._users.insert().values(username=username, password=get_password_hash(password),
                                              own_timezone=own_timezone)

        return self._execute_single_insert(_insert)

    def add_calendar(self, owner_id, calendar_name, calendar_color):
        _insert = self._calendars.insert().values(owner_id=owner_id, calendar_name=calendar_name,
                                                  calendar_color=calendar_color)

        return self._execute_single_insert(_insert)

    def add_event(self, calendar_id, event_name, event_description, start_time, end_time, event_timezone,
                  all_day_event):
        _insert = self._events.insert().values(calendar_id=calendar_id, event_name=event_name,
                                               event_description=event_description, start_time=start_time,
                                               end_time=end_time, event_timezone=event_timezone,
                                               all_day_event=all_day_event)

        return self._execute_single_insert(_insert)

    def add_share(self, calendar_id, user_id, write_permission):
        _insert = self._shares.insert().values(calendar_id=calendar_id, user_id=user_id,
                                               write_permission=write_permission)

        return self._execute_single_insert(_insert)

    def add_invite(self, event_id, user_id, is_owner=False):
        _insert = self._invites.insert().values(event_id=event_id, user_id=user_id, is_owner=is_owner)

        return self._execute_single_insert(_insert)

    def get_user_data(self, username):
        _select = self._users.select(self._users.c.username == username)

        return self._fetch_single_select(_select, lambda r: {"user_id": r[0], "username": r[1], "password": r[2],
                                                             "tz": r[3]})

    def get_users_like(self, like_string):
        _select = self._users.select(self._users.c.username.like('%' + like_string + '%'))

        return self._fetch_many_select(_select, lambda r: {"user_id": r[0], "username": r[1]})

    def get_user_calendars(self, user_id):
        _select = self._calendars.select(self._calendars.c.owner_id == user_id)

        own_calendars = self._fetch_many_select(_select, lambda r: {"calendar_id": r[0], "calendar_name": r[2],
                                                                    "calendar_color": r[3]})

        _alias = alias(
            select([self._calendars.c.calendar_id, self._calendars.c.calendar_name, self._calendars.c.owner_id,
                    self._calendars.c.calendar_color, self._shares.c.write_permission]).select_from(
                self._calendars.join(self._shares,
                                     self._calendars.c.calendar_id == self._shares.c.calendar_id)).where(
                self._shares.c.user_id == user_id), "sc")

        _select = select([self._users.c.username, _alias.c.calendar_id, _alias.c.calendar_name,
                          _alias.c.calendar_color, _alias.c.write_permission]).select_from(
            self._users.join(_alias,
                             self._users.c.user_id == _alias.c.owner_id))

        shared_calendars = self._fetch_many_select(_select, lambda r: {"owner": r[0], "calendar_id": r[1],
                                                                       "calendar_name": r[2], "calendar_color": r[3],
                                                                       "write_permission": r[4]})

        return {"my_calendars": own_calendars, "shared_with_me": shared_calendars}

    def get_user_calendar_privilege(self, user_id, calendar_id):
        _select = select([self._calendars.c.owner_id]).where(self._calendars.c.calendar_id == calendar_id)

        connection = self._engine.connect()

        result = connection.execute(_select).fetchone()

        if result is not None and result[0] == user_id:
            connection.close()
            return 3

        _select = select([self._shares.c.write_permission]).where(and_(self._shares.c.calendar_id == calendar_id,
                                                                       self._shares.c.user_id == user_id))

        result = connection.execute(_select)
        connection.close()

        if result.rowcount > 0:
            return 2 if result.fetchone()[0] else 1
        else:
            return 0

    def get_calendar_events(self, calendar_id):
        _select = select([self._events.c.event_id, self._events.c.event_name, self._events.c.start_time,
                          self._events.c.end_time, self._events.c.event_timezone, self._events.c.all_day_event,
                          self._events.c.event_description]). \
            where(self._events.c.calendar_id == calendar_id)

        return self._fetch_many_select(_select, lambda r: {"event_id": r[0], "event_name": r[1],
                                                           "start_time": set_utc(r[2]), "end_time": set_utc(r[3]),
                                                           "event_timezone": r[4], "all_day_event": r[5],
                                                           "event_description": r[6]})

    def get_invite(self, user_id, invite_id):
        _select = select([self._events.c.event_id, self._events.c.event_name, self._events.c.start_time,
                          self._events.c.end_time, self._events.c.event_timezone, self._events.c.all_day_event,
                          self._invites.c.invite_id, self._invites.c.is_owner, self._invites.c.has_edited,
                          self._invites.c.own_name, self._invites.c.own_start_time, self._invites.c.own_end_time,
                          self._invites.c.own_all_day_event, self._invites.c.attendance_status,
                          self._events.c.event_description, self._invites.c.own_description,
                          self._invites.c.own_timezone]). \
            select_from(self._events.join(self._invites)).where(
            and_(self._invites.c.user_id == user_id, self._invites.c.invite_id == invite_id))

        return self._fetch_single_select(_select,
                                         lambda r: {"event_id": r[0],
                                                    "event_name": r[9] if r[8] and r[9] is not None else r[1],
                                                    "start_time": set_utc(
                                                        r[10] if r[8] and r[10] is not None else r[2]),
                                                    "end_time": set_utc(r[11] if r[8] and r[11] is not None else r[3]),
                                                    "event_timezone": r[16] if r[8] and r[16] is not None else r[4],
                                                    "all_day_event": r[12] if r[8] and r[12] is not None else r[5],
                                                    "invite_id": r[6],
                                                    "is_owner": r[7],
                                                    "attendance": r[13],
                                                    "description": r[15] if r[8] and r[15] is not None else r[14]})

    def get_invites(self, user_id, archive=False):
        _or_clause = or_(self._events.c.end_time > datetime.utcnow() if not archive else
                             self._events.c.end_time < datetime.utcnow(),
                         self._invites.c.own_end_time > datetime.utcnow() if not archive else
                             self._invites.c.own_end_time > datetime.utcnow())

        _select = select([self._events.c.event_id, self._events.c.event_name, self._events.c.start_time,
                          self._events.c.end_time, self._events.c.event_timezone, self._events.c.all_day_event,
                          self._invites.c.invite_id, self._invites.c.is_owner, self._invites.c.has_edited,
                          self._invites.c.own_name, self._invites.c.own_start_time, self._invites.c.own_end_time,
                          self._invites.c.own_all_day_event, self._invites.c.attendance_status,
                          self._events.c.event_description, self._invites.c.own_description,
                          self._invites.c.own_timezone]). \
            select_from(self._events.join(self._invites)).where(
            and_(self._invites.c.user_id == user_id, _or_clause))

        return self._fetch_many_select(_select,
                                       lambda r: {"event_id": r[0],
                                                  "event_name": r[9] if r[8] and r[9] is not None else r[1],
                                                  "start_time": set_utc(r[10] if r[8] and r[10] is not None else r[2]),
                                                  "end_time": set_utc(r[11] if r[8] and r[11] is not None else r[3]),
                                                  "event_timezone": r[16] if r[8] and r[16] is not None else r[4],
                                                  "all_day_event": r[12] if r[8] and r[12] is not None else r[5],
                                                  "invite_id": r[6],
                                                  "is_owner": r[7],
                                                  "attendance": r[13],
                                                  "description": r[15] if r[8] and r[15] is not None else r[14]})

    def update_calendar(self, calendar_id, calendar_name, calendar_color):
        _update = self._calendars.update().where(self._calendars.c.calendar_id == calendar_id).\
            values(calendar_name=calendar_name, calendar_color=calendar_color)

        return self._execute_single_update_delete(_update)

    def update_event(self, event_id, event_name, event_description, start_time, end_time, event_timezone,
                     all_day_event):
        _update = self._events.update().where(self._events.c.event_id == event_id).\
            values(event_name=event_name, event_description=event_description, start_time=start_time, end_time=end_time,
                   event_timezone=event_timezone, all_day_event=all_day_event)

        return self._execute_single_update_delete(_update)

    def get_user_shares(self, user_id):
        _filtered_calendars = alias(select([self._calendars.c.calendar_name, self._calendars.c.calendar_color,
                                            self._calendars.c.calendar_id]).
                                    where(self._calendars.c.owner_id == user_id), "fc")
        _select = select([self._shares.c.share_id, self._shares.c.calendar_id, self._shares.c.user_id,
                          self._users.c.username, _filtered_calendars.c.calendar_name,
                          _filtered_calendars.c.calendar_color, self._shares.c.write_permission]). \
            select_from(self._shares.join(_filtered_calendars).join(self._users))

        return self._fetch_many_select(_select, lambda r: {"share_id": r[0], "calendar_name": r[4],
                                                           "calendar_color": r[5], "write_permission": r[6],
                                                           "shared_with": r[3]})

    def update_share(self, share_id, write_permission):
        _update = self._shares.update().where(self._shares.c.share_id == share_id).\
            values(write_permission=write_permission)

        return self._execute_single_update_delete(_update)

    def update_invite_description(self, user_id, invite_id, own_name, own_description, own_start_time, own_end_time,
                                  own_all_day_event):
        _update = self._invites.update().where(and_(self._invites.c.invite_id == invite_id,
                                                    self._invites.c.user_id == user_id)).\
            values(own_name=own_name, own_description=own_description, own_start_time=own_start_time,
                   own_end_time=own_end_time, own_all_day_event=own_all_day_event, has_edited=True)

        return self._execute_single_update_delete(_update)

    def restore_default_event_data(self, user_id, invite_id):
        _update = self._invites.update().where(and_(self._invites.c.invite_id == invite_id,
                                                    self._invites.c.user_id == user_id)). \
            values(own_name=None, own_description=None, own_start_time=None, own_end_time=None, own_all_day_event=None,
                   has_edited=False)

        return self._execute_single_update_delete(_update)

    def update_invite_attendance(self, user_id, invite_id, attendance):
        _update = self._invites.update().where(and_(self._invites.c.invite_id == invite_id,
                                                    self._invites.c.user_id == user_id)).\
            values(attendance_status=attendance)

        return self._execute_single_update_delete(_update)

    def delete_calendar(self, calendar_id):
        _delete = self._calendars.delete().where(self._calendars.c.calendar_id == calendar_id)

        return self._execute_single_update_delete(_delete)

    def delete_event(self, event_id):
        _delete = self._events.delete().where(self._events.c.event_id == event_id)

        return self._execute_single_update_delete(_delete)

    def delete_share(self, share_id):
        _delete = self._shares.delete().where(self._shares.c.share_id == share_id)

        return self._execute_single_update_delete(_delete)

    def get_event(self, event_id):
        _select = self._events.select(self._events.c.event_id == event_id)

        return self._fetch_single_select(_select, lambda r: {'event_id': r[0], 'event_name': r[2],
                                                             'event_description': r[3], 'start_time': set_utc(r[4]),
                                                             'end_time': set_utc(r[5]), 'event_timezone': r[6],
                                                             'all_day_event': r[7]})

    def get_calendar_id_for_event(self, event_id):
        _select = select([self._events.c.calendar_id]).where(self._events.c.event_id == event_id)

        return self._fetch_single_select(_select, lambda r: r[0])

    def get_calendar_id_for_share(self, share_id):
        _select = select([self._shares.c.calendar_id]).where(self._shares.c.share_id == share_id)

        return self._fetch_single_select(_select, lambda r: r[0])

    def get_invite_ownership(self, user_id, invite_id):
        _select = select([self._invites.c.is_owner]).where(and_(self._invites.c.invite_id == invite_id,
                                                                self._invites.c.user_id == user_id))

        return self._fetch_single_select(_select, lambda r: r[0])

    def get_event_id_for_invite(self, invite_id):
        _select = select([self._invites.c.event_id]).where(self._invites.c.invite_id == invite_id)

        return self._fetch_single_select(_select, lambda r: r[0])

    def get_event_guests(self, event_id):
        guests = {}

        for attendance_status, attendance_id in zip(['unknown', 'no', 'maybe', 'yes'], range(0, 4)):
            _alias = alias(select([self._invites.c.user_id]).where(
                and_(self._invites.c.event_id == event_id, self._invites.c.attendance_status == attendance_id)))
            _select = select([self._users.c.username]).select_from(self._users.join(_alias, _alias.c.user_id ==
                                                                                    self._users.c.user_id))

            guests[attendance_status] = self._fetch_many_select(_select, lambda r: r[0])

        return guests

    def get_invite_for_user_at_event(self, user_id, event_id):
        _select = self._invites.select(and_(self._invites.c.user_id == user_id, self._invites.c.event_id == event_id))

        return self._fetch_single_select(_select, lambda r: {'invite_id': r[0], 'is_owner': r[1], 'has_edited': r[2],
                                                             'attendance': r[3]})

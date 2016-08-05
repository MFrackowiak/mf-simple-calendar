import hashlib

from sqlalchemy import create_engine, Table, Column, Integer, DateTime, String, MetaData, ForeignKey, Boolean, \
    UniqueConstraint, select, alias
from sqlalchemy.sql import and_, or_
from sqlalchemy_utils import create_database, database_exists
from datetime import datetime

from .config import server_type, server_url, db_user, db_password, database_name, debug
from .var_utils import get_password_hash


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
                            Column('own_timezone', Integer, nullable=False))

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

    def _fetch_single_select(self, _select, mapping=None):
        connection = self._engine.connect()

        result = connection.execute(_select)

        connection.close()

        if result.rowcount < 1:
            raise ValueError("Zadany rekord nie istnieje w bazie danych.")

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

    def add_invite(self, event_id, user_id):
        _insert = self._invites.insert().values(event_id=event_id, user_id=user_id)

        return self._execute_single_insert(_insert)

    def get_user_data(self, username):
        _select = self._users.select(self._users.c.username == username)

        return self._fetch_single_select(_select, lambda r: {"user_id": r[0], "username": r[1], "password": r[2],
                                                             "tz": r[3]})

    def get_users_like(self, like_string):
        _select = self._users.select(self._users.c.username.like(like_string))

        return self._fetch_many_select(_select, lambda r: {"user_id": r[0], "username": r[1], "password": r[2],
                                                           "tz": r[3]})

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

        print(_alias)

        _select = select([self._users.c.username, _alias.c.calendar_id, _alias.c.calendar_name,
                          _alias.c.calendar_color, _alias.c.write_permission]).select_from(
            self._users.join(_alias,
                             self._users.c.user_id == _alias.c.owner_id))

        print(_select)

        shared_calendars = self._fetch_many_select(_select, lambda r: {"owner": r[0], "calendar_id": r[1],
                                                                       "calendar_name": r[2], "calendar_color": r[3],
                                                                       "write_permission": r[4]})

        return {"my_calendars": own_calendars, "shared_with_me": shared_calendars}

    def get_user_calendar_privilege(self, user_id, calendar_id):
        _select = select([self._calendars.c.user_id]).where(self._calendars.c.calendar_id == calendar_id)

        connection = self._engine.connect()

        if connection.execute(_select).fetchone()[0] == user_id:
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
                          self._events.c.end_time, self._events.c.event_timezone, self._events.c.all_day_event]). \
            where(self._events.c.calendar_id == calendar_id)

        return self._fetch_many_select(_select, lambda r: {"event_id": r[0], "event_name": r[1], "start_time": r[2],
                                                           "end_time": r[3], "event_timezone": r[4],
                                                           "all_day_event": r[5]})

    def get_invites(self, user_id, archive=False):
        # TODO timezones!
        _or_clause = or_(self._events.c.end_time > datetime.utcnow() if not archive else
                             self._events.c.end_time < datetime.utcnow(),
                         self._invites.c.own_end_time > datetime.utcnow() if not archive else
                             self._invites.c.own_end_time > datetime.utcnow())

        _select = select([self._events.c.event_id, self._events.c.event_name, self._events.c.start_time,
                          self._events.c.end_time, self._events.c.event_timezone, self._events.c.all_day_event,
                          self._invites.c.invite_id, self._invites.c.is_owner, self._invites.c.has_edited,
                          self._invites.c.own_name, self._invites.c.own_start_time, self._invites.c.own_end_time,
                          self._invites.c.own_all_day_event, self._invites.c.attendance_status]). \
            select_from(self._events.join(self._invites)).where(
            and_(self._invites.c.user_id == user_id, _or_clause))

        # TODO timezones in invites...?
        return self._fetch_many_select(_select,
                                       lambda r: {"event_id": r[0],
                                                  "event_name": r[9] if r[8] and r[9] is not None else r[1],
                                                  "start_time": r[10] if r[8] and r[10] is not None else r[2],
                                                  "end_time": r[11] if r[8] and r[11] is not None else r[3],
                                                  "timezone": r[4],
                                                  "all_day": r[12] if r[8] and r[12] is not None else r[5],
                                                  "invite_id": r[6],
                                                  "is_owner": r[7],
                                                  "attendance": r[13]})

    def update_calendar(self, calendar_id, calendar_name, calendar_color):
        pass

    def update_event(self, event_id, event_name, event_description, start_time, end_time, event_timezone,
                     all_day_event):
        pass

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
        pass

    def update_invite_description(self, user_id, invite_id, own_name, own_description, own_start_time, own_end_time,
                                  own_all_day_event):
        pass

    def update_invite_attendance(self, user_id, invite_id, attendance):
        pass

    def delete_calendar(self, calendar_id):
        pass

    def delete_event(self, event_id):
        pass

    def delete_share(self, share_id):
        pass

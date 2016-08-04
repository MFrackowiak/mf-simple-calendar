import hashlib

from sqlalchemy import create_engine, Table, Column, Integer, DateTime, String, MetaData, ForeignKey, Boolean
from sqlalchemy_utils import create_database, database_exists

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
                            Column('username', String(30), unique=True),
                            Column('password', String(64)),
                            Column('own_timezone', Integer))

        self._calendars = Table('calendars', metadata,
                                Column('calendar_id', Integer, primary_key=True),
                                Column('owner_id', Integer, ForeignKey('users.user_id')),
                                Column('calendar_name', String(30)),
                                Column('calendar_color', String(25)))

        self._events = Table('events', metadata,
                             Column('event_id', Integer, primary_key=True),
                             Column('calendar_id', Integer, ForeignKey('calendars.calendar_id')),
                             Column('event_name', String(30)),
                             Column('event_description', String(200)),
                             Column('start_time', DateTime),
                             Column('end_time', DateTime),
                             Column('event_timezone', Integer),
                             Column('all_day_event', Boolean))

        self._shares = Table('shares', metadata,
                             Column('share_id', Integer, primary_key=True),
                             Column('calendar_id', Integer, ForeignKey('calendars.calendar_id')),
                             Column('user_id', Integer, ForeignKey('users.user_id')),
                             Column('write_permission', Boolean))

        self._invites = Table('invites', metadata,
                              Column('invite_id', Integer, primary_key=True),
                              Column('event_id', Integer, ForeignKey('events.event_id')),
                              Column('user_id', Integer, ForeignKey('users.user_id')),
                              Column('is_owner', Boolean, default=False),
                              Column('has_edited', Boolean, default=False),
                              Column('own_name', String(30), nullable=True),
                              Column('own_description', String(200), nullable=True),
                              Column('own_start_time', DateTime, nullable=True),
                              Column('own_end_time', DateTime, nullable=True),
                              Column('own_all_day_event', Boolean, nullable=True),
                              Column('attendance_status', Integer, default=0))

        if create_new_if_needed:
            metadata.create_all(self._engine)

    def _get_engine(self):
        return create_engine("{type}://{user}:{pswd}@{host}/{name}".format(type=server_type, user=db_user, pswd=db_password,
                                                                           host=server_url, name=database_name),
                             encoding='utf8', echo=debug)

    def _execute_single_insert(self, _insert):
        connection = self._engine.connect()

        result = connection.execute(_insert)

        connection.close()

        return result.inserted_primary_key[0]

    def add_user(self, username, password, own_timezone):
        _insert = self._users.insert().values(username=username, password=get_password_hash(password),
                                              own_timezone=own_timezone)

        self._execute_single_insert(_insert)

    def add_calendar(self, owner_id, calendar_name, calendar_color):
        _insert = self._calendars.insert().values(owner_id=owner_id, calendar_name=calendar_name,
                                                  calendar_color=calendar_color)

        self._execute_single_insert(_insert)

    def add_event(self, calendar_id, event_name, event_description, start_time, end_time, event_timezone,
                  all_day_event):
        _insert = self._events.insert().values(calendar_id=calendar_id, event_name=event_name,
                                               event_description=event_description, start_time=start_time,
                                               end_time=end_time, event_timezone=event_timezone,
                                               all_day_event=all_day_event)

        self._execute_single_insert(_insert)

    def add_share(self, calendar_id, user_id, write_permission):
        _insert = self._shares.insert().values(calendar_id=calendar_id, user_id=user_id,
                                               write_permission=write_permission)

        self._execute_single_insert(_insert)

    def add_invite(self, event_id, user_id):
        _insert = self._invites.insert().values(event_id=event_id, user_id=user_id)

        self._execute_single_insert(_insert)

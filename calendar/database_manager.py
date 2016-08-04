import hashlib

from sqlalchemy import create_engine, Table, Column, Integer, DateTime, String, MetaData, ForeignKey, Boolean
from sqlalchemy_utils import create_database, database_exists

from .config import server_type, server_url, user, password, database_name, debug


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
                            Column('password', String(256)),
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
        return create_engine("{type}://{user}:{pswd}@{host}/{name}".format(type=server_type, user=user, pswd=password,
                                                                           host=server_url, name=database_name),
                             encoding='utf8', echo=debug)

    def create_user(self):
        pass
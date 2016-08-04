from calendar.database_manager import DatabaseManager
from datetime import datetime, timedelta


if __name__ == '__main__':
    try:
        db_manager = DatabaseManager(False)
    except ConnectionError as e:
        print(str(e))

    db_manager = DatabaseManager(True)

    u = db_manager.add_user("TestUser4", "VerySafePassword", 1)
    print(u)

    c = db_manager.add_calendar(1, "TestCalendar", "pink")
    print(c)

    e = db_manager.add_event(c, "TestEvent", "TestEventDescription", datetime.utcnow() + timedelta(days=1),
                             datetime.utcnow() + timedelta(days=1, seconds=3600 * 4), 0, False)
    print(e)

    s = db_manager.add_share(c, u, False)
    print(s)

    i = db_manager.add_invite(e, u)
    print(i)

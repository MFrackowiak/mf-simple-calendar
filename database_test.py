from calendar.database_manager import DatabaseManager
from datetime import datetime, timedelta


if __name__ == '__main__':
    try:
        db_manager = DatabaseManager(False)
    except ConnectionError as e:
        print(str(e))

    db_manager = DatabaseManager(True)

    test_add = False

    if test_add:
        u1 = db_manager.add_user("TestUser12", "VerySafePassword", 1)
        print(u1)

        u2 = db_manager.add_user("TestUser21", "VerySafePassword", 1)
        print(u2)

        c = db_manager.add_calendar(u1, "TestCalendar", "pink")
        print(c)

        e = db_manager.add_event(c, "TestEvent", "TestEventDescription", datetime.utcnow() + timedelta(days=1),
                                 datetime.utcnow() + timedelta(days=1, seconds=3600 * 4), 0, False)
        print(e)

        s = db_manager.add_share(c, u2, False)
        print(s)

        i = db_manager.add_invite(e, u2)
        print(i)

    print(db_manager.get_user_data("TestUser12"))
    print(db_manager.get_user_data("TestUser21"))

    db_manager.get_invites(1)

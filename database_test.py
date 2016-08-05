from calendar.database_manager import DatabaseManager
from datetime import datetime, timedelta

import random


if __name__ == '__main__':
    try:
        db_manager = DatabaseManager(False)
    except ConnectionError as e:
        print(str(e))

    db_manager = DatabaseManager(True)

    test_add_simple = False
    test_shares = False
    test_invites = False

    if test_add_simple:
        users = {}
        c = {}

        for i in range(4):
            users[db_manager.add_user("TestUser{}".format(i), "{}pword", i)] = {}

        for u in users:
            for i in range(2):
                users[u][db_manager.add_calendar(u, "TestCalendar{}_{}".format(u, i), "red")] = []

            for c in users[u]:
                for i in range(4):
                    users[u][c].append(db_manager.add_event(c, "TestEvent{}_{}_{}".format(u, c, i),
                                                            "TestDesc{}_{}_{}".format(u, c, i),
                                                            datetime.utcnow() + timedelta(days=i),
                                                            datetime.utcnow() + timedelta(days=i, seconds=3600),
                                                            0, False))

    users = db_manager.get_users_like("TestUser%")
    print(users)

    for u in users:
        id = u['user_id']
        cals = db_manager.get_user_calendars(id)

        print(cals)

        for c in cals['my_calendars']:
            events = db_manager.get_calendar_events(c['calendar_id'])
            print(events)

            if test_invites:
                for ev in events:
                    a = random.randint(0, len(users) - 1)
                    if users[a] != u:
                        db_manager.add_invite(ev['event_id'], users[a]['user_id'])

            if test_shares:
                a = random.randint(0, len(users) - 1)
                if users[a] != u:
                    db_manager.add_share(c['calendar_id'], users[a]['user_id'], random.randint(0, 1) == 1)

    print(db_manager.get_user_data("TestUser1"))
    print(db_manager.get_user_data("TestUser2"))

    invites = db_manager.get_invites(1, archive=False)
    print(invites)

from calendar_app.database_manager import DatabaseManager
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
    test_deletes = False

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
                        i = db_manager.add_invite(ev['event_id'], users[a]['user_id'])
                        db_manager.update_invite_attendance(users[a]['user_id'], i, random.randint(0, 3))

                    ev_id = ev['event_id']

            if test_shares:
                a = random.randint(0, len(users) - 1)
                if users[a] != u:
                    db_manager.add_share(c['calendar_id'], users[a]['user_id'], random.randint(0, 1) == 1)

    print(db_manager.get_user_data("TestUser1"))
    print(db_manager.get_user_data("TestUser2"))

    invites = db_manager.get_invites(1, archive=False)
    print("INVITES")
    print(invites)
    print("INVITES")

    shares = db_manager.get_user_shares(2)

    print(db_manager.update_share(shares[0]['share_id'], False if shares[0]['write_permission'] else True))

    ev = db_manager.get_calendar_events(db_manager.get_user_calendars(2)['my_calendars'][0]['calendar_id'])[0]
    print(ev)

    print(db_manager.update_event(ev['event_id'], ev['event_name'] + 'u', ev['event_description'] + 'u',
                                  ev['start_time'] + timedelta(seconds=60), ev['end_time'] + timedelta(seconds=60),
                                  ev['event_timezone'], ev['all_day_event']))

    ev = db_manager.get_calendar_events(db_manager.get_user_calendars(2)['my_calendars'][0]['calendar_id'])[0]
    print(ev)

    invite = invites[0]
    print(invite)

    db_manager.update_invite_attendance(1, invite['invite_id'], 1)
    print(db_manager.get_invites(1, False)[0])

    db_manager.update_invite_description(1, invite['invite_id'], None, "This is changed event desc",
                                         invite['start_time'] + timedelta(seconds=7200),
                                         invite['end_time'] + timedelta(seconds=7200),
                                         None)

    print(db_manager.get_invites(1, False)[0])

    db_manager.restore_default_event_data(1, invite['invite_id'])

    print(db_manager.get_invites(1, False)[0])

    if test_deletes:
        u = db_manager.add_user("TestUserDeleting", "123451235", 5)

        c = db_manager.add_calendar(u, "ToDeleteCalendar", "Pink")
        e = []

        for a in range(5):
            e.append(db_manager.add_event(c, "TD1", "TD1d", datetime.utcnow() + timedelta(seconds=3600),
                                          datetime.utcnow() + timedelta(seconds=6000), 0, False))

            db_manager.add_invite(e[-1], 1)

        s = db_manager.add_share(c, 1, 0)

        print(db_manager.get_user_calendars(1))
        print(db_manager.get_invites(1))

        for a in range(2):
            db_manager.delete_event(e[a])

        print(db_manager.get_invites(1))

        print(db_manager.delete_share(s))

        print(db_manager.get_user_calendars(1))
        print(db_manager.get_calendar_events(c))

        db_manager.delete_calendar(c)

        print(db_manager.get_user_calendars(u))

    events = db_manager.get_calendar_events(db_manager.get_user_calendars(2)['my_calendars'][0]['calendar_id'])

    for e in events:
        a = str(e['start_time'])
        print(a)

    print(db_manager.get_event_guests(5))

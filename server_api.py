from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, session

from calendar_app.calendar import Calendar  # calendar_app
from calendar_app.json_encoder import CustomJSONEncoder

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
calendar_app = Calendar()


@app.route("/test", methods=['POST'])
def test_datetime_parse():
    in_json = request.get_json()
    print(in_json)
    if 'tz' not in in_json or in_json['tz'] is None:
        d = datetime.strptime(in_json['date'], "%Y-%m-%d %H:%M:%S %z")
        print(d)
        print(d.astimezone(timezone(timedelta(hours=0))))
    else:
        d = datetime.strptime(in_json['date'],
                              "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=in_json['tz'])))
        print(d)
        print(d.astimezone(timezone(timedelta(hours=0))))
    return jsonify({'ok': True})


@app.route("/date", methods=['GET'])
def test_datetime_encode():
    return jsonify({'date': datetime.utcnow().replace(tzinfo=timezone(timedelta(hours=2)))})


@app.route("/user", methods=['PUT'])
def create_user():
    if session.get('user_id', None) is not None:
        ret_json = calendar_app.error_dict(1, "Need to logout before registering new user.")
    else:
        in_data = request.get_json()

        if in_data is None:
            ret_json = calendar_app.error_dict(4, "Request malformed.")
        else:
            try:
                ret_json = calendar_app.add_user(in_data['username'], in_data['password'], in_data['timezone'])

                if ret_json['success']:
                    session['user_id'] = ret_json['user_id']
                    session['user_tz'] = in_data['timezone']
            except KeyError:
                ret_json = calendar_app.error_dict(4, "Request malformed.")
            except Exception:
                ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/users/<str:like>", methods=['GET'])
def get_users_like(like):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            ret_json = calendar_app.get_users(like)
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/auth", methods=['POST'])
def auth_user():
    if session.get('user_id', None) is not None:
        ret_json = calendar_app.error_dict(1, "Need to logout before logging in.")
    else:
        in_data = request.get_json()

        if in_data is None:
            ret_json = calendar_app.error_dict(4, "Request malformed.")
        else:
            try:
                ret_json = calendar_app.authorize_user(in_data['username'], in_data['password'])

                if ret_json['success']:
                    session['user_id'] = ret_json['user_id']
                    session['user_tz'] = ret_json['tz']

                    ret_json = calendar_app.success_dict('auth', True)
            except KeyError:
                ret_json = calendar_app.error_dict(4, "Request malformed.")
            except Exception:
                ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/logout", methods=['POST'])
def logout_user():
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before logging out.")
    else:
        session.pop('user_id', None)
        session.pop('user_tz', None)

        ret_json = calendar_app.success_dict('logout', True)

    return jsonify(ret_json)


@app.route("/calendar", methods=['PUT'])
def create_calendar():
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            in_data = request.get_json()

            ret_json = calendar_app.add_calendar(session['user_id'], in_data['calendar_name'],
                                                 in_data['calendar_color'])
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/calendar/<int:calendar_id>", methods=['GET'])
def get_calendar_events(calendar_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            ret_json = calendar_app.get_events(session['user_id'], session['user_tz'], calendar_id)
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/calendar/<int:calendar_id>", methods=['POST', 'DELETE'])
def edit_delete_calendar(calendar_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            if request.method == 'POST':
                in_data = request.get_json()

                ret_json = calendar_app.edit_calendar(session['user_id'], calendar_id, in_data['calendar_name'],
                                                      in_data['calendar_color'])
            elif request.method == 'DELETE':
                ret_json = calendar_app.delete_calendar(session['user_id'], calendar_id)
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/calendar/<int:calendar_id>/share", methods=['PUT'])
def share_calendar(calendar_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            in_data = request.get_json()

            ret_json = calendar_app.share_calendar(session['user_id'], calendar_id, in_data['user_id'],
                                                   in_data['write_permission'])
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed, missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/calendars", methods=['GET'])
def get_calendars():
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            ret_json = calendar_app.get_calendars(session['user_id'])
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/shares", methods=['GET'])
def get_shares():
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            ret_json = calendar_app.get_shares(session['user_id'])
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/share/<int:share_id>", methods=['POST', 'DELETE'])
def edit_delete_share(share_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            if request.method == 'POST':
                in_data = request.get_json()

                ret_json = calendar_app.edit_share_permission(session['user_id'], share_id, in_data['write_permission'])
            elif request.method == 'DELETE':
                ret_json = calendar_app.delete_share(session['user_id'], share_id)
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/calendar/<int:calendar_id>/event", methods=['PUT'])
def create_event(calendar_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            in_data = request.get_json()

            ret_json = calendar_app.add_event(session['user_id'], calendar_id, in_data['event_name'],
                                              in_data['event_description'], in_data['start_time'],
                                              in_data['end_time'], in_data.get('event_timezone', None),
                                              in_data['all_day_event'])
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/event/<int:event_id>", methods=['GET', 'POST', 'DELETE'])
def get_edit_delete_event(event_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            if request.method == 'POST':
                in_data = request.get_json()

                ret_json = calendar_app.edit_event(session['user_id'], event_id, in_data['event_name'],
                                                   in_data['event_description'], in_data['start_time'],
                                                   in_data['end_time'], in_data.get('event_timezone', None),
                                                   in_data['all_day_event'])
            elif request.method == 'DELETE':
                ret_json = calendar_app.delete_event(session['user_id'], event_id)
            elif request.method == 'GET':
                ret_json = calendar_app.get_event(session['user_id'], session['user_tz'], event_id)
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/event/<int:event_id>/invite", methods=['PUT'])
def invite_for_event(event_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            in_data = request.get_json()

            ret_json = calendar_app.invite_user(session['user_id'], event_id, in_data['user_id'], False)
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/event/<int:event_id>/guests", methods=['GET'])
def get_event_guests(event_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            ret_json = calendar_app.get_guests(session['user_id'], event_id)
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/invite/<int:invite_id>/attendance", methods=['POST'])
def change_attendance_for_invite(invite_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            in_data = request.get_json()

            ret_json = calendar_app.edit_invite_attendance(session['user_id'], invite_id, in_data['attendance'])
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/invite/<int:invite_id>", methods=['POST', 'GET'])
def edit_invite(invite_id):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            if request.method == 'POST':
                in_data = request.get_json()

                ret_json = calendar_app.edit_invite(session['user_id'], invite_id, in_data.get('event_name', None),
                                                    in_data.get('event_description', None),
                                                    in_data.get('start_time', None), in_data.get('end_time', None),
                                                    in_data.get('event_timezone', None),
                                                    in_data.get('all_day_event', None))
            elif request.method == 'GET':
                ret_json = calendar_app.get_invite(session['user_id'], session['user_tz'], invite_id)
        except KeyError:
            ret_json = calendar_app.error_dict(4, "Request malformed. Missing data.")
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


@app.route("/invites", defaults={'archive': 0}, methods=['GET'])
@app.route("/invites/<int:archive>", methods=['GET'])
def get_invites(archive):
    if session.get('user_id', None) is None:
        ret_json = calendar_app.error_dict(1, "Need to log in before performing any action.")
    else:
        try:
            ret_json = calendar_app.get_invites(session['user_id'], session['user_tz'])
        except Exception:
            ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

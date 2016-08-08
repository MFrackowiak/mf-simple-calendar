from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, session

from calendar_app.calendar import calendar_app
from calendar_app.json_encoder import CustomJSONEncoder

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder


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
                user_dict = calendar_app.authorize_user(in_data['username'], in_data['password'])
                ret_json = calendar_app.add_user(in_data['username'], in_data['password'], in_data['timezone'])

                if ret_json['success']:
                    session['user_id'] = user_dict['user_id']
                    session['user_tz'] = user_dict['timezone']
            except KeyError:
                ret_json = calendar_app.error_dict(4, "Request malformed.")
            except Exception:
                ret_json = calendar_app.error_dict(5, "Server error.")

    return jsonify(ret_json)



@app.route("/logout", methods=['POST'])
def logout_user():
    pass


@app.route("/calendar", methods=['PUT'])
def create_calendar():
    pass


@app.route("/calendars", methods=['GET'])
def get_calendars():
    pass


@app.route("/shares", methods=['GET'])
def get_shares():
    pass


@app.route("/calendar/<int:calendar_id>", methods=['GET'])
def get_calendar_events(calendar_id):
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

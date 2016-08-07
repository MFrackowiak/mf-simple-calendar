from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

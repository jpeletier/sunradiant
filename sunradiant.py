from requests.auth import HTTPBasicAuth
import urllib
import requests
from subprocess import Popen, PIPE, STDOUT
from datetime import date, datetime, timedelta
import time

url = "https://www.tutiempo.net/radiacion-solar/madrid.html"
influxdb_url = "http://10.79.0.2:8086/write?db=homeassistant&precision=s"
influxdb_user = "javi"
influxdb_password = "influx79"

r = requests.get(url, allow_redirects=True)
open("/tmp/data.html", "wb").write(r.content)

# cat /tmp/data.html | pup 'div[id="HorasDia2"] span[class="hora"],div[id="HorasDia2"] strong text{}'

today = date.today()
raw_post = ""
for d in range(2, 16):
    p = Popen(
        [
            "pup",
            f'div[id="HorasDia{d}"] span[class="hora"],div[id="HorasDia{d}"] strong text{{}}',
        ],
        stdout=PIPE,
        stdin=PIPE,
        stderr=PIPE,
    )
    stdout_data = p.communicate(input=r.content)[0]
    raw_data = stdout_data.decode()
    arr_data = raw_data.split("\n")
    len_data = int((len(arr_data) - 1) / 2)

    tomorrow = today + timedelta(days=d - 1)

    radiance = []

    for i in range(0, len_data):
        hour = int(arr_data[i][:2])
        dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour)
        radiance.append((dt, int(arr_data[len_data + i])))

    auth = HTTPBasicAuth(influxdb_user, influxdb_password)
    for ri in radiance:
        epoch = int(time.mktime(ri[0].timetuple()))
        print(f"Irradiance value for {ri[0]} = {ri[1]} W/m²")
        raw_post = (
            raw_post
            + f"irradiance_prediction,unit_of_measurement=wm2 value={ri[1]} {epoch}\n"
        )

print("posting...")
result = requests.post(influxdb_url, data=raw_post, auth=auth)
if result.status_code != 204:
    print(
        f"Error posting data: status={result.status_code}, msg={result.content.decode() }"
    )
else:
    print("OK")

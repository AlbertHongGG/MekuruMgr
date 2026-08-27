import re

with open("src/providers/comicwifi/config.py", "r", encoding="utf-8") as f:
    c = f.read()

defaults = {
    "user_agent": '"ktor-client"',
    "device_id": '"2c9b9cb61659a16b"',
    "app_version": '"1.1.1"',
    "app_version_code": '"111"',
    "channel_no": '"3"',
    "app_channel": '"3"',
    "app_id": '"6"',
    "os_version": '"13"',
    "device_model": '"SM-A326BR"',
    "device_brand": '"samsung"',
    "device_make": '"samsung"',
    "screen_width": '"720"',
    "screen_height": '"1445"',
    "os_type": '"1"',
    "network_type": '"0"',
    "language": '"zh"',
    "device_language": '"zh"',
    "time_zone": '"GMT+08:00"',
    "lower_flow": '"No"',
    "imei": '""',
    "mac": '""',
    "oaid": '""',
    "userid": '"-1"',
    "token": '""',
    "isvpn": '""',
    "languagecode": '""'
}

for key, val in defaults.items():
    c = re.sub(rf"    {key}: str\n", f"    {key}: str = Field(default={val})\n", c)

with open("src/providers/comicwifi/config.py", "w", encoding="utf-8") as f:
    f.write(c)

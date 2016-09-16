import datetime
from constants import SHOW_LOGS

def print_log(msg, *args, **kwargs):
    if SHOW_LOGS:
        now = datetime.datetime.now()
        time_format = (now.year, now.month, now.day,
                       now.hour, now.minute, now.second)
        print("[{:02}-{:02}-{:02} {:02}:{:02}:{:02}]: {}".\
              format(*time_format, msg), *args, **kwargs)

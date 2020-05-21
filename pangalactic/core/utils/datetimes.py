"""
PGEF date-time convenience functions.
"""
from time import strptime
from datetime import timedelta, datetime, date, time

# pytz
import pytz

# tzlocal
from tzlocal import get_localzone


PGEF_FILE_DATETIME_FMT = '%Y-%m-%d-%H-%M'

def dtstamp():
    """
    Generate a naive datetime stamp for the current date and time.
    If converted to a string using str(), the datetime can be recovered from
    the string using datetime.fromisoformat().

    @return:  a datetime stamp for the current (UTC) date and time
    @rtype:   C{datetime}
    """
    return datetime.utcnow()

def file_dts():
    """
    Generate datetime stamp string that can be used in a file name.

    @return:  a datetime stamp string
    @rtype:   C{str}
    """
    return datetime.utcnow().strftime(PGEF_FILE_DATETIME_FMT)

def to_local_tz(naive_utc_dt):
    """
    Convert a naive UTC datetime stamp to a local datetime.
    """
    tz = get_localzone()
    return pytz.utc.localize(naive_utc_dt).astimezone(tz)


# NOTE:  legacy crap beyond this line ... some of it is still used  :(
# ************************************************************************

# datetime string formats
PGEF_TIME_FMT = '%H:%M:%S'
PGEF_DATE_FMT = '%Y-%m-%d'
PGEF_DATETIME_FMT = '%Y-%m-%d %H:%M:%S %Z'
PGEF_DATETIME_FMT_NO_TZ = '%Y-%m-%d %H:%M:%S'

PGEF_FANCY_DATE_FMT = '%a %d %b %Y'
PGEF_FANCY_DATETIME_FMT = '%a %d %b %Y %H:%M:%S %Z'
PGEF_FANCY_DATETIME_FMT_NO_TZ = '%a %d %b %Y %H:%M:%S'

# datetime constants
ZERO = timedelta(0)
HOUR = timedelta(hours=1)
EPOCH_DATE = date(1970, 1, 1)
EPOCH = datetime(1970, 1, 1)

def earlier(t1, t2):
    """
    Failure-proof version of 't1 < t2' -- works even if one of them is a
    datetime and the other is a date (use min time of date).  NOTE:  `None` is
    earlier than *anything* (including itself! :).

    Args:
        t1 (date or datetime):  to be determined if earlier
        t2 (date or datetime):  to be determined if later
    """
    if t1 is None:
        return True
    try:
        return t1 < t2
    except:
        if type(t1) is date:
            try:
                return datetime.combine(t1, time(0, 0)) < t2
            except:
                return False
        else:
            try:
                return t1 < datetime.combine(t2, time(0, 0))
            except:
                return False

def str2date(s):
    """
    Get a date object from a PGEF formatted date string (i.e., a string of the
    form yielded by date2str(date)).

    @param s:  a string in PGEF date format (C{PGEF_DATE_FMT})
    @type  s:  C{str}

    @return:  a date object representing the string date
    @rtype:   C{date}
    """
    retval = None
    if s:
        try:
            t = strptime(s, PGEF_DATE_FMT)
        except:
            try:
                t = strptime(s, PGEF_FANCY_DATE_FMT)
            except:
                try:
                    t = strptime(s, "%Y/%m/%d")
                except:
                    try:
                        t = strptime(s, "%m/%d/%Y")
                    except:
                        raise ValueError('unknown date format')
        retval = date(t.tm_year, t.tm_mon, t.tm_mday)
    return retval

def date2str(dt):
    """
    Get a PGEF formatted date string from a datetime object.

    @param dt:  a datetime object
    @type  dt:  C{datetime}

    @return:  a string in PGEF datetime format (C{PGEF_DATETIME_FMT})
    @rtype:   C{str}
    """
    retval = ''
    if dt:
        retval = dt.strftime(PGEF_DATE_FMT)
    return retval

def str2dt(s):
    """
    Get a datetime object from a PGEF formatted datetime string (i.e., a string
    of the form yielded by dt2str(datetime)).

    @param s:  a string in PGEF datetime format (C{PGEF_DATETIME_FMT})
    @type  s:  C{str}

    @return:  a datetime object representing the string datetime
    @rtype:   C{datetime}
    """
    # just in case something weird happened, like str(datetime)
    retval = None
    if s:
        if '+' in s:
            s = s.split('+')[0]
        try:
            t = strptime(s, PGEF_DATETIME_FMT)
            retval = datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour,
                              t.tm_min, t.tm_sec)
        except:
            try:
                t = strptime(s, PGEF_DATETIME_FMT_NO_TZ)
                retval = datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour,
                                  t.tm_min, t.tm_sec)
            except:
                ValueError, 'unrecognized datetime string format'
    return retval

def dt2str(dt):
    """
    Get a PGEF formatted datetime string from a datetime object.

    @param dt:  a datetime object
    @type  dt:  C{datetime}

    @return:  a string in PGEF datetime format (C{PGEF_DATETIME_FMT})
    @rtype:   C{str}
    """
    try:
        return dt.strftime(PGEF_DATETIME_FMT_NO_TZ)
    except:
        return ''

def dt2local_tz_str(dt):
    """
    Get a PGEF formatted datetime string from a datetime object converted to
    local time zone.

    @param dt:  a datetime object
    @type  dt:  C{datetime}

    @return:  a string in PGEF datetime format (C{PGEF_DATETIME_FMT})
    @rtype:   C{str}
    """
    try:
        return to_local_tz(dt).strftime(PGEF_DATETIME_FMT)
    except:
        return ''

def str2time(tstr, format=PGEF_TIME_FMT):
    """
    Get a Python time object from a string in PGEF time format.

    @return:  a string in PGEF time format (C{PGEF_TIME_FMT})
    @type  tstr:  C{str}
    """
    t = strptime(tstr, format)
    return time(t.tm_hour, t.tm_min, t.tm_sec)

def time2str(t):
    """
    Get a string in PGEF time format from an Python time object.

    @param t:  a Python time
    @type  t:  C{time.struct_time}
    """
    return t.isoformat()

def getDate(dt, format=PGEF_DATE_FMT):
    """
    Get a date string in PGEF date display format (C{PGEF_DATE_FMT}) from a
    Python datetime.datetime object.
    """
    return dt.strftime(format)


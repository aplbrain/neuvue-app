from django.core.validators import URLValidator
import json
from pytz import timezone
import pytz

def is_url(value):
    validate = URLValidator()
    try:
        validate(value)
        return True
    except:
        return False

def is_json(value):
    try:
        json.loads(value)
        return True
    except:
        return False

def utc_to_eastern(time_value):
    """Converts a pandas datetime object to a US/Easten datetime.

    Args:
        time_value (pd.DateTime): the timevalue you wish to convert

    Returns:
        DateTime: Datetime object
    """
    try:
        utc = pytz.UTC
        eastern = timezone('US/Eastern')
        date_time = time_value.to_pydatetime()
        date_time = utc.localize(time_value)
        return date_time.astimezone(eastern)
    except:
        return time_value
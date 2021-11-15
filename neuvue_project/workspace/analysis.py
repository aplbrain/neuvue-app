from datetime import datetime, date, timedelta
import numpy as np


def is_lastweek(timestamp):
    """Returns if the datetime provided is in the last week or not.

    Args:
        timestamp (pd.TimeStamp): Pandas timestamp object.

    Returns:
        bool: True if in last week
    """
    dt = timestamp.to_pydatetime()
    weekago = datetime.now() - timedelta(days=7)
    return weekago <= dt <= datetime.now()
    
def get_sum_time(table):
    seconds =  np.array([x['duration'] for x in table]).sum()
    hours = round(seconds/(60*60), 1)
    return hours
    
def get_rate(table):
    mean =  np.array([x['duration'] for x in table]).mean()
 
    if np.isnan(mean):
        return 0
    else:
        minutes = round(mean/(60))
        return minutes

def user_stats(table):
    # look at weekly stats
    weekly_table = [x for x in table if is_lastweek(x['closed'])]

    stats = {
        "total_tasks": len(table),
        "weekly_tasks": len(weekly_table),
        "total_time": get_sum_time(table),
        "weekly_time": get_sum_time(weekly_table),
        "total_rate": get_rate(table),
        "weekly_rate": get_rate(weekly_table)
    }
    
    return stats
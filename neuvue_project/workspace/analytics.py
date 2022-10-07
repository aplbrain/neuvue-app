from datetime import datetime, date, timedelta, timezone
from pytz import timezone
import pytz
import numpy as np
import pandas as pd

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)

def is_lastweek(timestamp):
    """Returns if the datetime provided is in the last week or not.

    Args:
        timestamp (pd.TimeStamp): Pandas timestamp object.

    Returns:
        bool: True if in last week
    """
    eastern = timezone('US/Eastern')
    
    dt = timestamp.to_pydatetime(warn=False)   # do not warn if nanoseconds are nonzero
    now = eastern.localize(datetime.now())
    weekago = now - timedelta(days=7)
    
    return weekago <= dt <= now
    
def get_sum_time(table):
    seconds =  np.array([x['duration'] for x in table]).sum()
    hours = round(seconds/(60*60), 1)
    return hours
    
def get_rate(table):

    durations = np.array([x['duration'] for x in table])

    if len(durations) > 0:
        mean =  durations.mean()
        minutes = round(mean/(60))
        return minutes
    else:
        return 0

def user_stats(table):
    # look at weekly stats
    weekly_table = [x for x in table if is_lastweek(x['closed'])]
    try:
        stats = {
            "total_tasks": len(table),
            "weekly_tasks": len(weekly_table),
            "total_time": get_sum_time(table),
            "weekly_time": get_sum_time(weekly_table),
            "total_rate": get_rate(table),
            "weekly_rate": get_rate(weekly_table)
        }
    except Exception as e:
        logging.error(f"Error computing analytics: {e}")
        stats = {
            "total_tasks": 'n/a',
            "weekly_tasks": 'n/a',
            "total_time": 'n/a',
            "weekly_time": 'n/a',
            "total_rate": 'n/a',
            "weekly_rate": 'n/a'
        }
    
    return stats

def create_stats_table(pending_tasks, closed_tasks):

    all_user_tasks = pd.concat([pending_tasks,closed_tasks])
    all_user_tasks = all_user_tasks[~all_user_tasks.index.duplicated(keep='first')].reset_index(drop=True)

    twentyFour_hrs_ago = datetime.now() - timedelta(days=1)
    daily_changelog_items = []
    full_changelog_items = []
    frames = [
        (daily_changelog_items, 'closed', all_user_tasks[all_user_tasks.closed >= twentyFour_hrs_ago]),
        (daily_changelog_items, 'created', all_user_tasks[all_user_tasks.created >= twentyFour_hrs_ago]),
        (full_changelog_items, 'closed', all_user_tasks[all_user_tasks.closed < twentyFour_hrs_ago]),
        (full_changelog_items, 'created', all_user_tasks[all_user_tasks.created < twentyFour_hrs_ago])
    ]

    for changelog, status, df in frames:
        for namespace, namespace_df in df.groupby('namespace'):
            n_tasks = len(namespace_df)
            m = namespace_df[status].min()
            average_event_time = (m + (namespace_df[status]-m)).mean().to_pydatetime()
            changelog.append((average_event_time, n_tasks, status, namespace))
    
    # Sort changelogs by datetime
    daily_changelog_items = sorted(daily_changelog_items, key=lambda x: x[0], reverse=True)
    full_changelog_items = sorted(full_changelog_items, key=lambda x: x[0], reverse=True)
    
    def generate_changelog_text(changelog_items):
        changelog_strings = [
            f"<li><b>{x[0].strftime('%m/%d/%Y, %H:%M:%S')}</b>: <code>{x[1]}</code> tasks {x[2]} from <code>{x[3]}</code></li>" 
            for x in changelog_items
            ]
        return '<ul>' + "\n".join(changelog_strings) + '</ul>'

    return generate_changelog_text(daily_changelog_items), generate_changelog_text(full_changelog_items)
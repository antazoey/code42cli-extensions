from py42.sdk.queries.alerts.alert_query import AlertQuery
from py42.sdk.queries.alerts.filters import DateObserved

from j42_util import get_default_search_timestamp


def create_simple_query():
    """Create a query to grab all alerts within the last 30 days."""
    start_date = get_default_search_timestamp()
    filters = [DateObserved.on_or_after(start_date)]
    query = AlertQuery.all(*filters)
    query.sort_direction = "asc"
    query.sort_key = "CreatedAt"
    return query


def get_alert_aggregate_data(sdk, alert_id):
    alert = sdk.alerts.get_aggregate_data(alert_id)
    return alert.data["alert"]

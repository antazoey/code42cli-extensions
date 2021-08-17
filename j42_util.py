import json
from datetime import datetime, timedelta, timezone

import click
import dateutil.parser


INITIALIZE_DAYS_BACK = 30


def get_now():
    return datetime.now(tz=timezone.utc)


def get_default_search_timestamp(days=INITIALIZE_DAYS_BACK):
    return (get_now() - timedelta(days=days)).timestamp()


def prettify_dict(data):
    return json.dumps(data, indent=2)


def output_pretty(data):
    data = prettify_dict(data)
    click.echo(data)


def parse_timestamp(date_str):
    # example: {"property": "bar", "timestamp": "2020-11-23T17:13:26.239647Z"}
    ts = date_str[:-1]
    date = dateutil.parser.parse(ts).replace(tzinfo=timezone.utc)
    return date.timestamp()


def print_numbered_list(items):
    """Outputs a numbered list of items to the user.
    For example, provide ["test", "foo"] to print "1. test\n2. foo".
    """

    choices = dict(enumerate(items, 1))
    for num in choices:
        click.echo(f"{num}. {choices[num]}")
    click.echo()

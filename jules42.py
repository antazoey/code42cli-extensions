import click
import json
import datetime

import code42cli.profile as cliprofile
from code42cli.extensions import script
from code42cli.extensions import sdk_options
from code42cli.util import parse_timestamp
from py42.exceptions import Py42ChecksumNotFoundError

from py42.sdk.queries.fileevents.file_event_query import FileEventQuery
from py42.sdk.queries.fileevents.filters.device_filter import OSHostname


@click.group(name="jules")
@sdk_options
def main(state):
    """My custom commands."""
    pass


@main.command()
@sdk_options
def list_managers(state):
    """Lists all managers along with their managed employees."""
    sdk = state.sdk
    users_generator = sdk.users.get_all()
    managers = {}
    for response in users_generator:
        users = response.data.get("users", [])
        for user in users:
            user_id = user["userUid"]
            username = user["username"]
            profile_response = sdk.detectionlists.get_user_by_id(user_id)
            manager_username = profile_response.data.get("managerUsername")
            if manager_username:
                if manager_username not in managers:
                    managers[manager_username] = [username]
                else:
                    managers[manager_username].append(username)

    json_text = _prettify_dict(managers)
    click.echo(json_text)


@main.command()
@sdk_options
def list_orgs(state):
    """Lists the organizations."""
    gen = state.sdk.orgs.get_all()
    for response in gen:
        org_list = response["orgs"]
        for org in org_list:
            data = json.dumps(org, indent=2)
            click.echo(data)


@main.command()
@sdk_options
@click.argument("org_id")
def show_org(state, org_id):
    """Show information about an Organization."""
    org = state.sdk.orgs.get_by_uid(org_id)
    data = json.dumps(org.data, indent=2)
    click.echo(data)


@main.command()
@sdk_options
def verify_audit_log_dates(state):
    """Seek for audit log event timestamp formats that we don't handle correctly."""
    gen = state.sdk.auditlogs.get_all()
    for response in gen:
        events = response["events"]
        for event in events:
            timestamp = event["timestamp"]
            try:
                parse_timestamp(timestamp)
            except ValueError:
                click.echo("FOUND ONE!")
                click.echo(event)


@main.command()
@sdk_options
def devices_health(state):
    """Show a device health report."""
    sdk = state.sdk
    generator = sdk.devices.get_all(include_backup_usage=True, active=True)
    for response in generator:
        devices = response["computers"]
        for device in devices:
            device_data = _create_device_data(sdk, device)
            click.echo(_prettify_dict(device_data))


def _create_device_data(sdk, device):
    device_name = device["name"]
    backup_usage = device.get("backupUsage", [])
    last_backup = _get_latest_backup_timestamp("lastBackup", backup_usage)
    last_completed_backup = _get_latest_backup_timestamp("lastCompletedBackup", backup_usage)
    archive_bytes = _get_max_archive_bytes(backup_usage)
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    last_security_event = _get_latest_security_event(sdk, device_name)
    return {
        "guid": device["guid"],
        "name": device_name,
        "lastConnected": device.get("lastConnected"),
        "lastBackup": last_backup,
        "lastCompletedBackup": last_completed_backup,
        "archiveBytes": archive_bytes,
        "healthCheckTime": current_time,
        "lastSecurityEvent": last_security_event
    }


def _get_latest_backup_timestamp(field_key, backup_usage):
    latest = (None, 0.0)
    for backup in backup_usage:
        timestamp = backup[field_key]
        if timestamp:
            parsed_timestamp = parse_timestamp(timestamp)
            if parsed_timestamp > latest[1]:
                latest = (timestamp, parsed_timestamp)
    return latest[0]


def _get_max_archive_bytes(backup_usage):
    archive_bytes = 0
    for backup in backup_usage:
        if backup["archiveBytes"] > archive_bytes:
            archive_bytes = backup["archiveBytes"]
    return archive_bytes


def _get_latest_security_event(sdk, device_name):
    device_filter = OSHostname.eq(device_name)
    query = FileEventQuery(device_filter)
    query.page_size = 1
    query.sort_key = "eventTimestamp"
    response = sdk.securitydata.search_file_events(query)
    file_events = response.data.get("fileEvents", [])
    if file_events:
        file_event = file_events[0]
        return {
            "eventTimestamp": file_event.get("eventTimestamp"),
            "eventType": file_event.get("eventType"),
            "fileName": file_event.get("fileName"),
            "md5Checksum": file_event.get("md5Checksum")
        }


@main.command()
@sdk_options
@click.option("--md5", help="The MD5 hash of the file to download.")
@click.option("--sha256", help="The SHA256 hash of the file to download.")
@click.option("--save-as", help="The name of the file to save as.", default="download")
def download(state, md5, sha256, save_as):
    """Download a file from Code42."""
    try:
        if md5:
            response = state.sdk.securitydata.stream_file_by_md5(md5)
        elif sha256:
            response = state.sdk.securitydata.stream_file_by_sha256(sha256)
        else:
            raise click.ClickException("Missing one of required md5 or sha256 options.")
    except Py42ChecksumNotFoundError as err:
        click.echo(str(err), err=True)
        return

    with open(save_as, "w") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(str(chunk))


@main.command()
def select():
    """Set a profile as the default by selecting it from a list."""
    profiles = cliprofile.get_all_profiles()
    profile_names = [profile_choice.name for profile_choice in profiles]
    choices = PromptChoice(profile_names)
    choices.print_choices()
    prompt_message = "Input the number of the profile you wish to use"
    profile_name = click.prompt(prompt_message, type=choices)
    _set_default_profile(profile_name)


class PromptChoice(click.ParamType):
    def __init__(self, choices):
        self.choices = choices

    def print_choices(self):
        print_numbered_list(self.choices)

    def convert(self, value, param, ctx):
        try:
            choice_index = int(value) - 1
            return self.choices[choice_index]
        except Exception:
            self.fail("Invalid choice", param=param)


def print_numbered_list(items):
    """Outputs a numbered list of items to the user.
    For example, provide ["test", "foo"] to print "1. test\n2. foo".
    """

    choices = dict(enumerate(items, 1))
    for num in choices:
        click.echo(f"{num}. {choices[num]}")
    click.echo()


def _set_default_profile(profile_name):
    cliprofile.switch_default_profile(profile_name)
    _print_default_profile_was_set(profile_name)


@main.command()
@sdk_options
@click.argument("alert_id")
def show_alert_details(state, alert_id):
    """Show an aggregated alert details view."""
    alert = state.sdk.alerts.get_aggregate_data(alert_id)
    data = _prettify_dict(alert.data)
    click.echo(data)


def _print_default_profile_was_set(profile_name):
    click.echo(f"{profile_name} has been set as the default profile.")


def _prettify_dict(data):
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    script.add_command(main)
    script()

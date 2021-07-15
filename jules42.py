import click
import json
import datetime

from code42cli.extensions import script
from code42cli.extensions import sdk_options
from code42cli.util import parse_timestamp

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


def _prettify_dict(data):
    return json.dumps(data, indent=2)


@main.command()
@sdk_options
#@click.argument("device_name")
def latest_device_event(state):
    """Show a device's latest security event via its device name."""
    # sdk = state.sdk
    # device_name.encode("utf-8")
    # latest_event = _get_latest_security_event(sdk, device_name)
    # click.echo(_prettify_dict(latest_event))


    test_device_name = "§§§§§¶•ººª••∞¢££™™¡ººª¶ª§"
    device_filter = OSHostname.eq(test_device_name)
    query = FileEventQuery(device_filter)
    response = state.sdk.securitydata.search_file_events(query)


if __name__ == "__main__":
    script.add_command(main)
    script()

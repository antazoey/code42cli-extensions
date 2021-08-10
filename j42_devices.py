from py42.sdk.queries.fileevents.file_event_query import FileEventQuery
from py42.sdk.queries.fileevents.filters import OSHostname

from j42_util import parse_timestamp, get_now


def create_device_data(sdk, device):
    device_name = device["name"]
    backup_usage = device.get("backupUsage", [])
    last_backup = _get_latest_backup_timestamp("lastBackup", backup_usage)
    last_completed_backup = _get_latest_backup_timestamp(
        "lastCompletedBackup", backup_usage
    )
    archive_bytes = _get_max_archive_bytes(backup_usage)
    current_time = get_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    last_security_event = _get_latest_security_event(sdk, device_name)
    return {
        "guid": device["guid"],
        "name": device_name,
        "lastConnected": device.get("lastConnected"),
        "lastBackup": last_backup,
        "lastCompletedBackup": last_completed_backup,
        "archiveBytes": archive_bytes,
        "healthCheckTime": current_time,
        "lastSecurityEvent": last_security_event,
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
            "md5Checksum": file_event.get("md5Checksum"),
        }

import click
import json

from code42cli.extensions import script
from code42cli.extensions import sdk_options
from code42cli.util import parse_timestamp


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
def find_audit_log_date(state):
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


def _prettify_dict(data):
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    script.add_command(main)
    script()

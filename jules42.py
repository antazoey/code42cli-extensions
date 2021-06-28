import click

from code42cli.extensions import script
from code42cli.extensions import sdk_options


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

    for manager in managers:
        managed_employees_str = ", ".join(managers[manager])
        output_str = f"{manager}: {managed_employees_str}"
        click.echo(output_str)


if __name__ == "__main__":
    script.add_command(main)
    script()

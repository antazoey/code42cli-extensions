import click
import code42cli.profile as cliprofile


def set_default_profile(profile_name):
    cliprofile.switch_default_profile(profile_name)
    print_default_profile_was_set(profile_name)


def print_default_profile_was_set(profile_name):
    click.echo(f"{profile_name} has been set as the default profile.")

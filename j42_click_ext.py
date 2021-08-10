import click
from j42_util import print_numbered_list


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

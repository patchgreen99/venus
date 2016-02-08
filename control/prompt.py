import traceback

from control.commands import Commands


def run_prompt():
    commands = Commands()
    text = raw_input('> ')
    while text != 'exit':
        tokens = text.split()
        if tokens:
            try:
                getattr(commands, tokens[0])(*tokens[1:])
            except:
                traceback.print_exc()
        text = raw_input('> ')

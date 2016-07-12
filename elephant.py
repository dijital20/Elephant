import logging
import os
import shlex
import sys

from ElephantBrain import ElephantBrain, AddledBrainError
from ElephantTrunk import ElephantTrunk


# Logger and formatter
log = logging.getLogger('Elephant')
log.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# File handler
fle = logging.FileHandler('Elephant.log')
fle.setLevel(logging.DEBUG)
fle.setFormatter(fmt)
if fle not in log.handlers:
    log.addHandler(fle)
# Console handler
cns = logging.StreamHandler()
cns.setLevel(logging.ERROR)
cns.setFormatter(fmt)
if cns not in log.handlers:
    log.addHandler(cns)


class TrumpetError(Exception):
    pass


class ElephantTrumpet(object):
    """
    ElephantTrumpet aims to be a command processor for the command line
    elephant interface. This should allow expanding command over all of the
    Elephant faculties.

    Fields:
        interactive (bool): True if we're running in interactive mode,
            False if not. Defaults to False.
        brain (None, ElephantBrain): Our open datafile. Defaults to None. Set
            by command_open, and unset by command_close.
    """
    def __init__(self):
        """
        Prepare an ElephantTrumpet object for use.
        """
        self.interactive = False
        self.brain = None

    @property
    def commands(self):
        """
        Returns a list of command methods supported (methods beginning with
        'command_').
        """
        return [m[8:] for m in dir(self) if m.startswith('command_')]

    def __prompt(self, prompt_string, accepted_vals, lower=True):
        """
        Continually prompt until an accepted value is reached.

        Args:
            prompt_string (str): Prompt to display to the user.
            accepted_vals (list): A list of accepted values.
            lower (bool): Should we lower-case the response before checking?
                Defaults to True.
        """
        while True:
            response = raw_input(prompt_string)
            if lower:
                response = response.lower()
            if response in accepted_vals:
                return response
            print('Accepted responses are: {0}\n'
                  'Please try again.'.format(
                ', '.join(accepted_vals)))

    def parse_commands(self, commands):
        """
        Parse the list of command strings and call the appropriate command
        method if it exists. Otherwise, tell the user he has an invalid
        command and print the help.

        Args:
            commands (str): Command list as a string.
        """
        command_list = shlex.split(commands)
        # print('Command_list: {0}'.format(command_list))
        call_command = command_list.pop(0)
        if call_command in self.commands:
            return getattr(
                self, 'command_{0}'.format(call_command)
            )(command_list)
        else:
            print('Invalid command: {0}'.format(call_command))
            return self.command_help([])

    def command_help(self, parm_list):
        """
        Print the help.

        Args:
            parm_list (list): An empty list. We don't use it, so honestly,
                it doesn't matter.
        """
        print('Type \'<Command> --help\' for more information on using a '
              'specific command.\n'
              'Commands available: {0}\n'.format(
            ', '.join(self.commands)))
        if self.interactive:
            print('Use \'quit\' to exit interactive mode.')

    def command_open(self, parm_list):
        """
        Open a file for editing. This file is assigned to self.brain.

        Args:
            parm_list (list): List of parameters to use.
        """
        print('Open: {0}'.format(parm_list))
        if '--help' in parm_list:
            print('Open a database for usage.\n'
                  '\n'
                  'Usage: open <path to database> [new]\n'
                  '\n'
                  'path to database: the path to the database file to open.\n'
                  'new: If new is specified, a new file will be created, '
                  'overwriting any existing file.')
            return None
        db_path = os.path.abspath(parm_list.pop(0))
        new = False
        if 'new' in parm_list:
            new = True
            parm_list.remove('new')
        if self.brain:
            print('The following file is open: {0}'.format(
                self.brain.file_path))
            close_file = self.__prompt(
                'Close this file: [Y/n]: ', ['y', 'n', ''], lower=True)
            if close_file in ['y', '']:
                self.command_close([])
            elif close_file == 'n':
                print('Leaving file alone then.')
                return None
        try:
            self.brain = ElephantBrain(db_path, new=new)
            print('Opened: {0}\n'.format(db_path))
            print(self.brain.info)
        except AddledBrainError as e:
            print('ERROR: The database failed to open: {0}'.format(e))
        except Exception as e:
            print('ERROR: An unexpected error happened: {0}'.format(e))

    def command_close(self, parm_list):
        """
        Close the active database.

        Args:
            parm_list (list): The params to pass.
        """
        print('Close: {0}'.format(parm_list))
        if not self.brain:
            print('No file currently opened.')
        else:
            old_brain = self.brain.file_path
            del(self.brain)
            self.brain = None
            print('Closed: {0}'.format(old_brain))

    def command_report(self, parm_list):
        """
        Run a report.

        Args:
            parm_list (list): The params to pass.
        """
        print('Report: {0}'.format(parm_list))


if __name__ == '__main__':
    trumpet = ElephantTrumpet()
    if len(sys.argv) > 1:
        # Command line mode
        trumpet.parse_commands(' '.join(sys.argv[1:]))
    else:
        # Interactive mode
        trumpet.interactive = True
        print('Starting elephant in interactive mode.\n')
        while True:
            command_string = raw_input('> ')
            if command_string.strip() == 'quit':
                break
            trumpet.parse_commands(command_string)
            print('')

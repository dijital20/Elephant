import logging
import os
import shlex
import sys

import ElephantLog

from ElephantBrain import ElephantBrain, AddledBrainError
from ElephantTrunk import ElephantTrunk


ElephantLog.init_log()


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

    def __param_dict(self, params, true_parms=[], false_parms=[]):
        """
        Convert a list of parameters into a dictionary.

        Args:
            params (list): List if entered parameters.
            true_parms (list): List of parameters that should result in a
                True value.
            false_parms (list): List of parameters that should result in a
                False value.

        Returns (dict):
        Dictionary of commands with their values. Also contains a special one
        called args which contain positional arguments.
        """
        command_dict = {'args': []}
        while params:
            p = params.pop(0)
            if str(p).startswith('-'):
                p = p.lstrip('-')
                if p not in command_dict:
                    command_dict[p] = []
                if p in true_parms:
                    command_dict[p].append(True)
                elif p in false_parms:
                    command_dict[p].append(False)
                else:
                    command_dict[p].append(params.pop(0))
            else:
                command_dict['args'].append(p)
        for k in command_dict:
            # Skip args. That should always be a list.
            if k == 'args':
                continue
            # If there's only one item, delist it.
            if len(command_dict[k]) == 1:
                command_dict[k] = command_dict[k][0]
            # If the list is all booleans, get their all() value.
            elif all([type(v) is bool for v in command_dict[k]]):
                command_dict[k] = all(command_dict[k])
        return command_dict

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
              'Commands available: {0}\n'.format(', '.join(self.commands)))
        if self.interactive:
            print('Use \'quit\' to exit interactive mode.')

    def command_open(self, parm_list):
        """
        Open a file for editing. This file is assigned to self.brain.

        Args:
            parm_list (list): List of parameters to use.
        """
        cmds = self.__param_dict(parm_list, true_parms=['new'])
        if cmds.get('help', False):
            print('Open a database for usage.\n'
                  '\n'
                  'Usage: open <path to database> [new]\n'
                  '\n'
                  'path to database: the path to the database file to open.\n'
                  'new: If new is specified, a new file will be created, '
                  'overwriting any existing file.')
            return None
        db_path = os.path.abspath(cmds['args'][0])
        new = cmds.get('new', False)
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
            print('Opening: {0}, New: {1}'.format(db_path, new))
            self.brain = ElephantBrain(db_path, new=new)
            print('Opened: {0}\n'.format(db_path))
            print(self.brain.info)
        except AddledBrainError as e:
            print('ERROR: The database failed to open: {0}'.format(e))
        except Exception as e:
            print('ERROR: An unexpected error happened: {0}'.format(e))

    def command_save(self, parm_list):
        if self.brain:
            if self.brain.save():
                print('{0} has been saved.'.format(self.brain))
            else:
                print('{0} encountered an error saving.'.format(self.brain))
        else:
            print('No file currently opened.')

    def command_close(self, parm_list):
        """
        Close the active database.

        Args:
            parm_list (list): The params to pass.
        """
        if not self.brain:
            print('No file currently opened.')
            return None
        old_brain = self.brain.file_path
        del(self.brain)
        self.brain = None
        print('Closed: {0}'.format(old_brain))

    def command_get(self, parm_list):
        cmds = self.__param_dict(parm_list, true_parms=['new'])
        if cmds.get('help', False):
            print('')
            return None
        if not self.brain:
            print('No file currently opened.')
            return None

    def command_add(self, parm_list):
        cmds = self.__param_dict(parm_list, true_parms=['new'])
        if cmds.get('help', False):
            print('')
            return None
        if not self.brain:
            print('No file currently opened.')
            return None

    def command_update(self, parm_list):
        cmds = self.__param_dict(parm_list, true_parms=['new'])
        if cmds.get('help', False):
            print('')
            return None
        if not self.brain:
            print('No file currently opened.')
            return None

    def command_delete(self, parm_list):
        cmds = self.__param_dict(parm_list, true_parms=['new'])
        if cmds.get('help', False):
            print('')
            return None
        if not self.brain:
            print('No file currently opened.')
            return None

    def command_info(self, parm_list):
        cmds = self.__param_dict(parm_list)
        if cmds.get('help', False):
            print('Gets information on the currently opened file.')
            return None
        if not self.brain:
            print('No file currently opened.')
            return None
        print(self.brain.info)

    def command_import(self, parm_list):
        cmds = self.__param_dict(parm_list)
        if cmds.get('help', False):
            print('')
            return None
        if not self.brain:
            print('No file currently opened.')
            return None
        if not all([p in cmds for p in ['table', 'file']]) \
                and all([type(cmds[p]) is str for p in cmds]):
            print('You must specify both a single table and a single file. '
                  'Use --help for more details.')
            return None
        table = cmds['table']
        file_path = os.path.abspath(cmds['file'])
        file_type = os.path.splitext(os.path.basename(file_path))[-1]
        if cmds['table'] not in ElephantBrain.schema:
            print('Table \'{0}\' is not a valid table. Valid options are: '
                  '{1}'.format(cmds['table'], ', '.join(ElephantBrain.schema)))
            return None
        if not os.path.isfile(file_path):
            print('File {0} does not exist.'.format(file_path))
            return None
        print('table: {0}\nfile: {1}\ntype: {2}'.format(
            table, file_path, file_type))
        if file_type == '.csv':
            self.brain.add_csv(table, file_path)
        elif file_type == '.xlsx':
            self.brain.add_xlsx(table, file_path)
        else:
            print('No idea what to do with file type {0}. '
                  'File should be xlsx or csv.'.format(file_type))

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

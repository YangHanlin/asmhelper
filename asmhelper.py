# Note: Ideally this script should only work on Windows.


import argparse
import json
import os
import re
import shutil
import sys
import subprocess

program_version = 'v0.0.1'
default_config = '`/default.json'
user_config = '~/.config/asmhelper/config.json'
configuration = {}
configuration_only = ['dosbox', 'recipes', 'broken', 'source-without-extension']
additional_path_expansion_needed = ['task-template']
additional_config_expansion_needed = []
configuration_schema = {
    'dosbox': {
        'path': '',
        'args': ('', [''])
    },
    'task-path': '',
    'recipes': [
        {
            'id': '',
            'commands': [(
                {
                    'type': ('host', 'dosbox'),
                    'command': ('', [''])
                },
                {
                    'type': 'recipe',
                    'recipe': (0, '')
                }
            )]
        },
    ]
}
message_levels = [
    ('info', sys.stderr),
    ('warning', sys.stderr),
    ('error', sys.stderr)
]


def main() -> None:
    load_configuration()
    if configuration['fix-config']:
        message('Fixing configuration')
        fix_config_file()
    else:
        recipe = configuration['recipes'][configuration['recipe']]
        message('Running recipe \'{}\''.format(recipe['id']))
        run_recipe(recipe)


def expand_path(path: str) -> str:
    return os.path.expanduser(path.replace('`', configuration['program-path']))


def run_recipe(recipe: dict) -> None:
    recipe_commands = recipe['commands']
    while True:
        recipe_replacement = []
        for i in range(len(recipe_commands)):
            command_group = recipe_commands[i]
            if command_group['type'] == 'recipe':
                if type(command_group['recipe']) == str:
                    found = False
                    for j in range(len(configuration['recipes'])):
                        if configuration['recipes'][j]['id'] == command_group['recipe']:
                            recipe_replacement.append((i, j))
                            found = True
                            break
                    if not found:
                        try:
                            recipe_index = int(command_group['recipe'])
                            if recipe_index not in range(len(configuration['recipes'])):
                                message('Invalid referenced recipe index {}'.format(recipe_index), level=2)
                                sys.exit(1)
                            recipe_replacement.append((i, recipe_index))
                            found = True
                        except ValueError:
                            message('Cannot find referenced recipe \'{}\''.format(command_group['recipe']), level=2)
                            sys.exit(1)
                elif type(command_group['recipe'] == int):
                    recipe_index = command_group['recipe']
                    if recipe_index not in range(len(configuration['recipes'])):
                        message('Invalid referenced recipe index {}.'.format(recipe_index), level=2)
                        sys.exit(1)
                    recipe_replacement.append((i, recipe_index))
        if recipe_replacement:
            replaced_commands = recipe_commands[:recipe_replacement[0][0]] \
                                + configuration['recipes'][recipe_replacement[0][1]][
                                    'commands']
            for i in range(1, len(recipe_replacement)):
                replaced_commands.extend(recipe_commands[recipe_replacement[i - 1][0] + 1:recipe_replacement[i][0]])
                replaced_commands.extend(configuration['recipes'][recipe_replacement[i][1]]['commands'])
            recipe_commands = replaced_commands
        else:
            break
    for command_group in recipe_commands:
        commands = []
        if type(command_group['command']) == str:
            commands = [command_group['command'].format(**configuration)]
        elif type(command_group['command'] == list):
            commands = [command.format(**configuration) for command in command_group['command']]
        if command_group['type'] == 'host':
            for command in commands:
                print('> {}'.format(command))
                return_code = os.system(command)
                if return_code:
                    message('The previous command seems to have encountered an error ({}).'.format(return_code),
                            level=1)
        elif command_group['type'] == 'dosbox':
            task_script = ''
            with open(configuration['task-template'], 'r', encoding='utf-8') as template_file:
                task_script = generate_task(commands, template_file.read())
            if os.path.exists(configuration['task-path']):
                task_path_renamed = configuration['task-path'] + '.bak'
                n = 0
                while os.path.exists(task_path_renamed):
                    n += 1
                    task_path_renamed = configuration['task-path'] + '.bak.' + str(n)
                os.rename(configuration['task-path'], task_path_renamed)
                message('Task script {} already exists; renamed to {}'
                        .format(configuration['task-path'], task_path_renamed), level=1)
            with open(configuration['task-path'], 'w', encoding='utf-8') as task_file:
                task_file.write(task_script)
            print('> Opening DOSBox <')
            return_code = subprocess.run(
                [configuration['dosbox']['path']] + configuration['dosbox']['args']).returncode
            print('> DOSBox has exited <')
            if return_code:
                message('DOSBox seems to have encountered an error ({}).'.format(return_code), level=1)
        else:
            message('Unsupported runtime type \'{}\' of command group'.format(command_group['type']), level=2)
            sys.exit(1)


def generate_task(commands: list, template: str) -> str:
    line_groups = [[]]
    res = ''
    for line in template.split('\n'):
        if line.lower().startswith('rem _asmhelper_repeat'):
            line_groups.append([])
        else:
            line_groups[-1].append(line)
    for i in range(len(line_groups)):
        if i % 2:
            for command in commands:
                configuration['_command'] = command
                res += '\n'.join(line_groups[i] + ['']).format(**configuration)
            del configuration['_command']
        else:
            res += '\n'.join(line_groups[i] + ['']).format(**configuration)
    return res


def load_configuration() -> None:
    configuration['program-path'] = sys.path[0]
    configuration['program-name'] = os.path.split(sys.argv[0])[-1]
    configuration['program-version'] = program_version
    configuration['broken'] = False
    if not os.path.exists(expand_path(user_config)):
        fix_config_file()
    with open(expand_path(user_config), 'r', encoding='utf-8') as file:
        config = json.load(file)
        if not parse_configuration(config):
            configuration['broken'] = True
    if not parse_commandline_args():
        message('An error occurred when parsing commandline arguments', level=2)
        sys.exit(1)
    if configuration['broken']:
        if not configuration['fix-config']:
            message('Configuration file {} may have been broken'.format(user_config), level=2)
            message('Use {} -f/--fix-config to try fixing it'.format(configuration['program-name']))
            sys.exit(1)
    else:
        if not polish_configuration():
            message('An error occurred when checking arguments', level=2)
            sys.exit(1)


def polish_configuration() -> bool:
    for i in range(len(configuration['recipes'])):
        if configuration['recipes'][i]['id'] == configuration['recipe']:
            configuration['recipe'] = i
            break
    if type(configuration['recipe']) != int:
        try:
            recipe = int(configuration['recipe'])
            if recipe not in range(len(configuration['recipes'])):
                message('Invalid recipe index {}'.format(recipe), level=2)
                return False
            configuration['recipe'] = recipe
        except ValueError:
            message('Cannot find recipe \'{}\''.format(configuration['recipe']), level=2)
            return False
    dot_index = configuration['source'].rfind('.')
    configuration['source-without-extension'] = configuration['source'] \
        if dot_index == -1 \
        else configuration['source'][:dot_index]
    if 'task-template' not in configuration or not configuration['task-template']:
        configuration['task-template'] = '`/task.bat.template'
    if 'path-expansion-needed' not in configuration:
        configuration['path-expansion-needed'] = []
    if type(configuration['path-expansion-needed']) != list:
        message('Invalid configuration for \'path-expansion-needed\'', level=2)
        return False
    configuration['path-expansion-needed'] = list(set(
        configuration['path-expansion-needed'] + additional_path_expansion_needed))
    for needed in configuration['path-expansion-needed']:
        if needed in configuration:
            configuration[needed] = expand_path(configuration[needed])
    if 'config-expansion-needed' not in configuration:
        configuration['path-expansion-needed'] = []
    if type(configuration['config-expansion-needed']) != list:
        message('Invalid configuration for \'config-expansion-needed\'', level=2)
        return False
    configuration['config-expansion-needed'] = list(set(
        configuration['config-expansion-needed'] + additional_config_expansion_needed))
    for needed in configuration['config-expansion-needed']:
        if needed in configuration:
            configuration[needed] = configuration[needed].format(**configuration)
    return True


def parse_configuration(config) -> bool:
    if not validate_configuration(config, configuration_schema):
        return False
    configuration.update(config)
    return True


def validate_configuration(config, schema) -> bool:
    if type(schema) == tuple:
        for option in schema:
            if validate_configuration(config, option):
                return True
        return False
    else:
        if type(config) != type(schema):
            return False
        if schema:
            if type(schema) == dict:
                for key in schema:
                    if key not in config or not validate_configuration(config[key], schema[key]):
                        return False
                return True
            elif type(schema) == list:
                for item in config:
                    if not validate_configuration(item, schema[0]):
                        return False
                return True
            elif type(schema) == str:
                return re.fullmatch(schema, config) is not None
        return True


def parse_commandline_args() -> bool:
    raw_args, rest = init_parser().parse_known_args()
    args = vars(raw_args)
    for key in args:
        configuration[key.replace('_', '-')] = args[key]
    for i in range(len(rest)):
        if rest[i].startswith('--') and len(rest[i]) > 2:
            arg = rest[i][2:]
            if arg not in configuration_only:
                configuration[arg] = rest[i + 1] \
                    if i < len(rest) - 1 and not rest[i + 1].startswith('--') \
                    else True
            else:
                message('Customized addition arg {} can only be accepted from configuration file', level=1)
    return True


def init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=configuration['program-name'],
        description='A simple script to build & run assembly programs in DOSBox.',
        allow_abbrev=False)
    parser.add_argument('source', metavar='SOURCE',
                        help='the source file being dealt with (i.e. assembling & debugging)')
    parser.add_argument('-r', '--recipe', metavar='ID/INDEX', default='0',
                        help='the recipe used to perform tasks, specified by its id or index in'
                             'the \'recipes\' array; the first recipe is used when omitted')
    parser.add_argument('-f', '--fix-config', action='store_true',
                        help='try fixing your configuration by restoring to default.')
    parser.add_argument('-V', '--version', action='version',
                        version='{program-name} {program-version} from {program-path}'.format(**configuration),
                        help='show version information and exit')
    return parser


def message(msg: str, level=0, *args, **kwargs) -> None:
    print('{}: {}: {}'.format(
        configuration['program-name'],
        message_levels[level][0],
        msg
    ), file=message_levels[level][1], *args, **kwargs)


def fix_config_file() -> None:
    dest = expand_path(user_config)
    dest_dir = os.path.split(dest)[0]
    src = expand_path(default_config)
    if os.path.exists(dest):
        dest_backup = dest + '.bak'
        n = 0
        while os.path.exists(dest_backup):
            n += 1
            dest_backup = dest + '.bak.' + str(n)
        os.rename(dest, dest_backup)
        message('User configuration file {} already exists; renamed to {}'.format(dest, dest_backup), level=1)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(src, dest)
    message('User configuration has been set to default')


if __name__ == '__main__':
    main()

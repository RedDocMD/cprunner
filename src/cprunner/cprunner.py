import argparse
import re
import pathlib
import os.path
import json
import sys
import subprocess
import tempfile
import shlex
import difflib
import io
from termcolor import colored


class ConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Command:
    def __init__(self, command):
        self.command = command

    def __str__(self):
        return self.command

    def _replacement(self, part, filename):
        if part == 'filename':
            return filename
        elif part == 'filenameWithoutExt':
            parent = filename.parent
            name = pathlib.PurePath(filename.stem)
            return parent/name
        elif part == 'fileDir':
            return filename.parent
        else:
            raise ConfigError(f'Invalid variable: ${{{part}}}')

    def __call__(self, filename):
        reg = re.compile(r'\$\{(\w+)\}')
        matches = reg.findall(self.command)
        if len(matches) == 0:
            return self.command
        else:
            final_command = self.command
            for part in matches:
                final_command = final_command.replace(
                    f'${{{part}}}', str(self._replacement(part, filename)))
            return final_command


class Language:
    def __init__(self, name, extensions, commands):
        self.name = name
        self.extensions = extensions
        self.commands = commands

    def __str__(self):
        return f"Language [name: {self.name}, extensions = {self.extensions}, commands = {self.commands}]"


class Config:
    def __init__(self, json_ob):
        self.languages = []
        self.ext_lang_map = {}
        for lang_key in json_ob:
            info = json_ob[lang_key]
            extensions = info["ext"]
            commands = [Command(command) for command in info["commands"]]
            language = Language(lang_key, extensions, commands)
            self.languages.append(language)
            for ext in extensions:
                if ext in self.ext_lang_map:
                    raise ConfigError(
                        f"Extension \"{ext}\" assigned more than once")
                self.ext_lang_map[ext] = language

    def __str__(self):
        out = ""
        for lang in self.languages:
            out += f"{lang}\n"
        return out

    def __getitem__(self, ext):
        return self.ext_lang_map[ext]


class ConfigNotFound(Exception):
    pass


def config_locations():
    short_path_segments = [['.cphelper.json'],
                           ['.config', 'cphelper.json'],
                           ['.config', 'cphelper', 'config.json']]
    short_paths = [pathlib.PurePath(*segments)
                   for segments in short_path_segments]
    home = pathlib.Path.home()
    long_paths = [home/path for path in short_paths]
    return long_paths


def get_config():
    locations = config_locations()
    for location in locations:
        if location.exists():
            with open(location) as file:
                return Config(json.load(file))
    raise ConfigNotFound()


def key_comb():
    if sys.platform == 'win32':
        return 'Ctrl + Z'
    else:
        return 'Ctrl + D'


def perform_diff(obtained_output):
    print(
        colored(f'\nEnter the expected output (then hit {key_comb()}):', 'yellow'))
    expected_output = sys.stdin.read()
    split_obtained = [s + '\n' for s in obtained_output.split('\n')]
    split_expected = [s + '\n' for s in expected_output.split('\n')]
    diff_stream = io.StringIO()
    diff_stream.writelines(difflib.context_diff(
        split_obtained, split_expected, fromfile='obtained', tofile='expected'))
    diff_contents = diff_stream.getvalue()
    if len(diff_contents) != 0:
        print(colored('\nMismatch found!', 'red'))
        print(diff_contents)
    else:
        print(colored('\nNo Mismatch found!', 'green'))


def execute(command, take_input=False, diff=False):
    proc = subprocess.Popen(shlex.split(command), text=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if take_input:
        print(colored(f"Enter the input (then hit {key_comb()}):", 'yellow'))
        inp = sys.stdin.read()
        proc.stdin.write(inp)

    out, err = proc.communicate()

    if len(out) > 0:
        print(colored('\nOutput obtained:', 'green'))
        print(out, end='')
    if len(err) > 0:
        print(colored('\nError obtained:', 'red'))
        print(err)
    proc.stdin.close()

    if diff:
        perform_diff(out)

    return proc.returncode


def executor():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("file", help="file you want to run")
        runtype_group = parser.add_mutually_exclusive_group()
        runtype_group.add_argument(
            "-r", "--run", help="Just run the code (default)", action="store_true")
        runtype_group.add_argument(
            "-d", "--diff", help="Run the code and diff with expected output", action="store_true")
        args = parser.parse_args()

        config = get_config()
        cwd = pathlib.Path.cwd()
        filename_path = pathlib.PurePath(args.file)
        filename_abs = (cwd/filename_path).resolve()

        ext = filename_abs.suffix[1:]
        lang = config[ext]
        for (i, command) in enumerate(lang.commands):
            last = i == len(lang.commands) - 1
            diff = args.diff and last
            actual_command = command(filename_abs)
            ret_code = execute(actual_command, last, diff)
            if ret_code != 0:
                break
    except ConfigNotFound:
        print(colored('No config file found', 'red'))
    except ConfigError as e:
        print(colored(f'Error in config file: {e}', 'red'))
    except Exception as e:
        print(colored(e, 'red'))

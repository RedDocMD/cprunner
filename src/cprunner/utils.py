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
from config import Config, ConfigError


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

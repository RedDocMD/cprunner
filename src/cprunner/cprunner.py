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
import pickle
from datetime import datetime
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


class CacheEntry:
    def __init__(self, given_inp, exp_out, timestamp):
        self.given_inp = given_inp
        self.exp_out = exp_out
        self.timestamp = timestamp

    def __str__(self):
        return f'CacheEntry: {self.timestamp}'


class Cache:
    _entry_lim = 100
    _cache_file = pathlib.Path.home() / pathlib.PurePath('.cprunner.cache')

    def __init__(self):
        self.entries = {}

    def __enter__(self):
        self._read_from_disk()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._write_to_disk()

    def _read_from_disk(self):
        if Cache._cache_file.exists():
            with open(Cache._cache_file, 'rb') as f:
                cache = pickle.load(f)
                self.entries = cache.entries

    def _write_to_disk(self):
        with open(Cache._cache_file, 'wb') as f:
            pickle.dump(self, f)

    def __getitem__(self, filename):
        if filename in self.entries:
            return self.entries[filename]
        else:
            return None

    def save(self, filename, given_inp, exp_out=None):
        timestamp = datetime.today()
        entry = CacheEntry(given_inp, exp_out, timestamp)
        if filename not in self.entries and len(self.entries) >= Cache._entry_lim:
            items = list(self.entries.items)
            items.sort(key=lambda it: it[1].timestamp)
            rem_key = items[0][0]
            del self.entries[rem_key]
        self.entries[filename] = entry


def config_locations():
    short_path_segments = [['.cprunner.json'],
                           ['.config', 'cprunner.json'],
                           ['.config', 'cprunner', 'config.json']]
    short_paths = [pathlib.PurePath(*segments)
                   for segments in short_path_segments]
    home = pathlib.Path.home()
    long_paths = [home/path for path in short_paths]
    long_paths.reverse()
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


def perform_diff(obtained_output, filename, cache, read_cache):
    entry = None
    if read_cache:
        entry = cache[filename]
    if entry is None or entry.exp_out is None:
        print(
            colored(f'\nEnter the expected output (then hit {key_comb()}):', 'yellow'))
        expected_output = sys.stdin.read()
    else:
        expected_output = entry.exp_out
        print(colored(f'\nTaking expected output as', 'yellow'))
        print(expected_output)

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
    return expected_output


def execute(command, filename, cache, read_cache, take_input=False, diff=False):
    proc = subprocess.Popen(shlex.split(command), text=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    save_entry = False
    if take_input:
        entry = None
        if read_cache:
            entry = cache[filename]
        if entry is None:
            print(
                colored(f"Enter the input (then hit {key_comb()}):", 'yellow'))
            inp = sys.stdin.read()
            save_entry = True
        else:
            inp = entry.given_inp
            print(colored('Taking input as:', 'yellow'))
            print(inp, end='')

    if take_input:
        proc.stdin.write(inp)
    out, err = proc.communicate()

    if len(out) > 0:
        print(colored('\nOutput obtained:', 'green'))
        print(out, end='')
    if len(err) > 0:
        print(colored('\nError obtained:', 'red'))
        print(err)
    proc.stdin.close()

    exp_out = None
    if diff:
        exp_out = perform_diff(out, filename, cache, read_cache)
        save_entry = True

    if save_entry:
        cache.save(filename, inp, exp_out)

    return proc.returncode


def executor():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("file", help="file you want to run")
        parser.add_argument(
            "-i", "--ignore", help="Ignore the cache entry for this file", action='store_true')
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
        with Cache() as cache:
            for (i, command) in enumerate(lang.commands):
                last = i == len(lang.commands) - 1
                diff = args.diff and last
                actual_command = command(filename_abs)
                ret_code = execute(
                    actual_command, filename_abs, cache, not args.ignore, last, diff)
                if ret_code != 0:
                    break
    except ConfigNotFound:
        print(colored('No config file found', 'red'))
    except ConfigError as e:
        print(colored(f'Error in config file: {e}', 'red'))
    except Exception as e:
        print(colored(e, 'red'))

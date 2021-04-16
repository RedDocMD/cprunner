#!/usr/bin/env python
import argparse
import pathlib
import os.path
import json
import re
import sys
import subprocess
import tempfile
import shlex


def config_locations():
    short_path_segments = [['.cphelper.json'],
                           ['.config', 'cphelper.json'],
                           ['.config', 'cphelper', 'config.json']]
    short_paths = [pathlib.PurePath(*segments)
                   for segments in short_path_segments]
    home = pathlib.Path.home()
    long_paths = [home/path for path in short_paths]
    return long_paths


class ConfigError(Exception):
    def __init__(self, message):
        super(message)


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
    def __init__(self, name, extensions, command):
        self.name = name
        self.extensions = extensions
        self.command = command

    def __str__(self):
        return f"Language [name: {self.name}, extensions = {self.extensions}, command = {self.command}]"


class Config:
    def __init__(self, json_ob):
        self.languages = []
        self.ext_lang_map = {}
        for lang_key in json_ob:
            info = json_ob[lang_key]
            extensions = info["ext"]
            command = Command(info["command"])
            language = Language(lang_key, extensions, command)
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


def get_config():
    locations = config_locations()
    for location in locations:
        if location.exists():
            with open(location) as file:
                return Config(json.load(file))
    raise ConfigNotFound()


def execute(command):
    if sys.platform == 'win32':
        key_comb = 'Ctrl + Z'
    else:
        key_comb = 'Ctrl + D'
    print(f"Enter the input (then hit {key_comb}):")
    inp = sys.stdin.read()
    proc = subprocess.Popen(shlex.split(
        command), text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proc.stdin.write(inp)
    out, err = proc.communicate()
    print('\nOutput obtained:')
    print(out, end='')
    proc.stdin.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="file you want to run")
    runtype_group = parser.add_mutually_exclusive_group()
    runtype_group.add_argument(
        "-r", "--run", help="Just run the code", action="store_true")
    runtype_group.add_argument(
        "-d", "--run-diff", help="Run the code and diff with expected output", action="store_true")
    args = parser.parse_args()

    config = get_config()
    cwd = pathlib.Path.cwd()
    filename_path = pathlib.PurePath(args.file)
    filename_abs = (cwd/filename_path).resolve()

    ext = filename_abs.suffix[1:]
    lang = config[ext]
    actual_command = lang.command(filename_abs)

    execute(actual_command)

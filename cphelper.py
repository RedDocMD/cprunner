#!/usr/bin/env python
import argparse
import pathlib
import os.path
import json


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
    pass


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
            command = info["command"]
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


class ConfigNotFound(Exception):
    pass


def get_config():
    locations = config_locations()
    for location in locations:
        if location.exists():
            with open(location) as file:
                return Config(json.load(file))
    raise ConfigNotFound()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="file you want to run")
    runtype_group = parser.add_mutually_exclusive_group()
    runtype_group.add_argument(
        "-r", "--run", help="Just run the code", action="store_true")
    runtype_group.add_argument(
        "-d", "--run-diff", help="Run the code and diff with expected output", action="store_true")
    args = parser.parse_args()

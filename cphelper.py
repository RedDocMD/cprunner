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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="file you want to run")
    runtype_group = parser.add_mutually_exclusive_group()
    runtype_group.add_argument(
        "-r", "--run", help="Just run the code", action="store_true")
    runtype_group.add_argument(
        "-d", "--run-diff", help="Run the code and diff with expected output", action="store_true")
    args = parser.parse_args()

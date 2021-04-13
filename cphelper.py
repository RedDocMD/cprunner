#!/usr/bin/env python
import argparse


def config_locations():
    short_paths = ['.cphelper.json', '.config/cphelper.json',
                   '.config/cphelper/config.json']


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="file you want to run")
    runtype_group = parser.add_mutually_exclusive_group()
    runtype_group.add_argument(
        "-r", "--run", help="Just run the code", action="store_true")
    runtype_group.add_argument(
        "-d", "--run-diff", help="Run the code and diff with expected output", action="store_true")
    args = parser.parse_args()

import argparse
import pathlib
from termcolor import colored
from config import ConfigError
from utils import get_config, execute, ConfigNotFound


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

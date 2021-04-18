# CP Runner

![PyPI](https://img.shields.io/pypi/v/cprunner)
![Status](https://img.shields.io/pypi/status/cprunner)

A helper "script" to quickly run your competitive programs and diff it against the expected output.

![terminal_img](./assets/cprunner1x.svg)

## Quick Start

Install from PyPI.

```shell
python3 -m pip install cprunner
```

Then get the default config file from the repo:

- On Linux/Mac:

```shell
wget -O ~/.cprunner.json https://raw.githubusercontent.com/RedDocMD/cprunner/main/config.json
```

- On Windows, on the [Windows Terminal](https://github.com/microsoft/terminal) or on Powershell (get wget [here](http://gnuwin32.sourceforge.net/packages/wget.htm)):

```shell
wget -O "$HOME\.cprunner.json" https://raw.githubusercontent.com/RedDocMD/cprunner/main/config.json
```

Finally run it on your program as:

```shell
cpr -d A.cpp
```

## Usage

```shell
❯ python src/cprunner -h                                    
usage: cprunner [-h] [-i] [-r | -d] file

positional arguments:
  file          file you want to run

optional arguments:
  -h, --help    show this help message and exit
  -i, --ignore  Ignore the cache entry for this file
  -r, --run     Just run the code (default)
  -d, --diff    Run the code and diff with expected output
```

## Configuration

CP Runner requires a JSON config file to know what command to run for what file extension.

### File locations

The config file can be at one of the following locations:

1. `$HOME/.config/cprunner/config.json`
2. `$HOME/.config/cprunner.json1`
3. `$HOME/.cprunner.json`

If more than one these files are present, then the one first in this list is considered.

### Format

The config file is of the following format (example [here](./config.json)):

```json
{
  "name1": {
    "ext": ["ext1", "ext2", "ext3"],
    "command": ["command1", "command2"]
  },
  "name2" : {
    "ext": ["ext4", "ext5"],
    "command": ["command3"]
  }
}
```

- **name** - This is a name given to that particular entry and has no significance beyond that
- **ext** - This is the list of extensions of files which are to be handled by this entry. _No extension can appear more than once_. This applies across different entries. An extension is specified **without** the leading dot.
- **command** - This is the list of commands that are executed for the specified extensions. Note that, _input is taken only for the last command_. So the program must be executed in the last step. The use of multiple commands is for languages that need to be compiled first and then run. Also, do not use combinators like `&&`, `||`, etc.

For each command in the `command` array, the following placeholders are defined:

- `filename`: The complete filename that is passed as an arg to the script
- `filenameWithoutExt`: The filename with extension removed
- `fileDir`: The directory of the file which is passed as arg.

A placeholder can be used as `${placeholder}`.

## Cache

CP Runner caches the inputs given by the user for the last 100 unique files it was run on. On subsequent runs, it fetches the input from its cache instead of asking the user for input. This expedites the debugging process. The cache is *presistent*. To ignore the cache entry and provide input again, pass the `-i` flag.

## Platforms

The script entirely uses platform-independent Python code. It should run on most platforms. I have tested it on Linux and by extension should work on Mac. I have no reason to believe that it won't work on Windows. If you find bugs, please report it [here](https://github.com/RedDocMD/cprunner/issues).

## License

Copyright (©) 2021 Deep Majumder

This software is distributed under the GNU General Public License v3 (GPLv3).

For more information, please read [LICENSE](./LICENSE).

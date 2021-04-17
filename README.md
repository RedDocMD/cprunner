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

- On Windows, on the [Windows Terminal](https://github.com/microsoft/terminal) (get wget [here](http://gnuwin32.sourceforge.net/packages/wget.htm)):

```shell
wget -O %HOMEPATH%\.cprunner.json https://raw.githubusercontent.com/RedDocMD/cprunner/main/config.json
```

Finally run it on your program as:

```shell
cpr -d A.cpp
```

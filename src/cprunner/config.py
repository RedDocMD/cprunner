import pathlib
import re


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

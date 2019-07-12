from dataclasses import dataclass
import util
from typing import List, Dict
import logging
import tex
import subprocess
from subprocess import DEVNULL
from pathlib import Path
import base64
import imaging


class SymbolError(Exception):
    pass


@dataclass
class SymbolCommandArgument:
    name: str
    code: str


@dataclass
class SymbolCommand:
    name: str
    code: str
    arguments: List[List[SymbolCommandArgument]]


@dataclass
class SymbolPackage:
    name: str
    font_encoding: str
    commands: List[SymbolCommand]


@dataclass
class SymbolDatabase:
    packages: List[SymbolPackage]


SYMBOL_DATABASE = util.load_json('symbols.json', SymbolDatabase)


@dataclass
class RenderedSymbolCommandArgument:
    name: str
    image: str


@dataclass
class RenderedSymbolCommand:
    name: str
    image: str
    arguments: List[List[RenderedSymbolCommandArgument]]


@dataclass
class RenderedSymbolPackage:
    name: str
    commands: List[RenderedSymbolCommand]


@dataclass
class RenderedSymbolDatabase:
    packages: List[RenderedSymbolPackage]


def build_render_code(package):
    def build_render_code_fragment(lines, code):
        lines.append("\\begin{center}")
        lines.append(code)
        lines.append("\\end{center}")

    lines = []
    lines.append(
        "\\documentclass[preview, varwidth,margin=3pt, multi=yes]{standalone}")
    lines.append("\\standaloneenv{center}")
    lines.append("\\usepackage[utf8]{inputenc}")
    lines.append(f"\\usepackage[{package.font_encoding}]{{fontenc}}")
    if package.name != '':
        lines.append(f"\\usepackage{{{package.name}}}")
    lines.append("\\begin{document}")
    for command in package.commands:
        if command.code:
            build_render_code_fragment(lines, command.code)

        for parameter in command.arguments:
            for argument in parameter:
                build_render_code_fragment(lines, argument.code)
    lines.append('\\end{document}')
    return '\n'.join(lines)


def count_symbols(package):
    symbol_count = 0
    for command in package.commands:
        if command.code:
            symbol_count += 1
        for parameter in command.arguments:
            symbol_count += len(parameter)
    return symbol_count


def render_package(package):
    display_name = package.name or 'kernel'
    symbol_count = count_symbols(package)
    logging.info('Rendering symbols of package "%s" (%i symbols)',
                 display_name, symbol_count)

    latex_result = tex.compile(build_render_code(package), timeout=60)
    dvi_path = latex_result.find('dvi')
    if not dvi_path.exists():
        logging.error('Failed to render package "%s" (compilation error)\nLog:\n%s',
                      display_name, latex_result.read_log())
        raise SymbolError()

    dvipng_cmd = ['dvipng', '-D', '4096', str(dvi_path)]
    dvipng_result = subprocess.run(dvipng_cmd, cwd=latex_result.tmpdir.name,
                                   stdout=DEVNULL, stderr=DEVNULL)
    dvipng_result.check_returncode()

    images = []
    for i in range(symbol_count):
        logging.debug('Cropping image %i', i + 1)
        image = latex_result.find_img(i + 1)
        imaging.crop_and_scale(image)
        images.append(base64.b64encode(image.read_bytes()).decode('utf-8'))

    image_index = 0
    commands = []
    for command in package.commands:
        command_image = None
        if command.code:
            command_image = images[image_index]
            image_index += 1

        all_arguments = []
        for parameter in command.arguments:
            arguments = []
            for argument in parameter:
                argument_image = images[image_index]
                image_index += 1
                arguments.append(
                    RenderedSymbolCommandArgument(argument.name, argument_image))
            all_arguments.append(arguments)

        commands.append(RenderedSymbolCommand(
            command.name, command_image, all_arguments))

    return RenderedSymbolPackage(package.name, commands)


def render_database():
    return RenderedSymbolDatabase([render_package(package)
                                   for package in SYMBOL_DATABASE.packages])

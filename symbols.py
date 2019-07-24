from dataclasses import dataclass
import util
from typing import List, Dict, Optional
import logging
import tex
import subprocess
from subprocess import DEVNULL
from pathlib import Path
import base64
import imaging
from tqdm import tqdm
import sys


@dataclass
class UnrenderedSymbolCommandArgument:
    name: str
    code: str


@dataclass
class UnrenderedSymbolCommand:
    name: str
    code: Optional[str]
    parameters: List[List[UnrenderedSymbolCommandArgument]]


@dataclass
class UnrenderedSymbolPackage:
    name: Optional[str]
    font_encoding: str
    commands: List[UnrenderedSymbolCommand]

    def render(self):
        rendered_package = SymbolPackage(self.name)
        latex_result = tex.compile(self._build_render_code(), timeout=60)
        self._render_images(latex_result)
        images = self._load_images(latex_result)
        image_index = 0
        for cmd in self.commands:
            cmd_image = None
            if cmd.code:
                cmd_image = images[image_index]
                image_index += 1

            rendered_cmd = SymbolCommand(cmd.name, cmd_image)
            for parameter in cmd.parameters:
                args = []
                for arg in parameter:
                    arg_image = images[image_index]
                    image_index += 1
                    args.append(SymbolCommandArgument(arg.name, arg_image))
                rendered_cmd.parameters.append(args)

            rendered_package.commands.append(rendered_cmd)
        return rendered_package

    def _build_render_code_header(self, lines):
        lines.append(
            "\\documentclass[preview, varwidth,margin=3pt, multi=yes]{standalone}")
        lines.append("\\standaloneenv{center}")
        lines.append("\\usepackage[utf8]{inputenc}")
        lines.append(f"\\usepackage[{self.font_encoding}]{{fontenc}}")
        if self.name:
            lines.append(f"\\usepackage{{{self.name}}}")

    def _build_render_code(self):
        def build_fragment(lines, code):
            lines.append("\\begin{center}")
            lines.append(code)
            lines.append("\\end{center}")

        lines = []
        self._build_render_code_header(lines)
        lines.append("\\begin{document}")
        for command in self.commands:
            if command.code:
                build_fragment(lines, command.code)

            for parameter in command.parameters:
                for argument in parameter:
                    build_fragment(lines, argument.code)

        lines.append('\\end{document}')
        return '\n'.join(lines)

    def _render_images(self, latex_result):
        display_name = self.name or "kernel"
        dvi_path = latex_result.find('dvi')
        if not dvi_path.exists():
            logging.error('Failed to render symbols of package "%s"\nLog:\n%s',
                          display_name, latex_result.read_log())
            sys.exit(-1)

        dvipng_cmd = ['dvipng', '-D', '4096', str(dvi_path)]
        dvipng_result = subprocess.run(dvipng_cmd, cwd=latex_result.tmpdir.name,
                                       stdout=DEVNULL, stderr=DEVNULL)
        dvipng_result.check_returncode()

    def _count_symbols(self):
        count = 0
        for command in self.commands:
            if command.code:
                count += 1
            for parameter in command.parameters:
                count += len(parameter)
        return count

    def _load_images(self, latex_result):
        symbol_count = self._count_symbols()
        images = []
        for i in range(symbol_count):
            logging.debug('Cropping image %i', i + 1)
            image = latex_result.find_img(i + 1)
            imaging.crop_and_scale(image)
            images.append(base64.b64encode(image.read_bytes()).decode('utf-8'))
        return images


@dataclass
class UnrenderedSymbolDatabase:
    packages: List[UnrenderedSymbolPackage]

    def render(self):
        packages = []
        for package in tqdm(self.packages, desc='Rendering symbols'):
            packages.append(package.render())
        return packages


SYMBOL_DATABASE = util.load_json('symbols.json', UnrenderedSymbolDatabase)


class SymbolCommandArgument:
    def __init__(self, name, image):
        self.name = name
        self.image = image


class SymbolCommand:
    def __init__(self, name, image):
        self.name = name
        self.image = image
        self.parameters = []


class SymbolPackage:
    def __init__(self, name):
        self.name = name
        self.commands = []

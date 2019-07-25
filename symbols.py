from base64 import b64encode
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
from tqdm import tqdm
from typing import List, Dict, Optional
import util
import logging
import tex
import base64
import pdf2image


SYMBOL_SIZE = (48, 48)
SYMBOL_PADDING = 5


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
        result = tex.compile(self._build_render_code(), timeout=60, pdf=True)
        pdf_path = result.find('pdf')
        images = [self._postprocess_image(img)
                  for img in pdf2image.convert_from_path(str(pdf_path), dpi=4096)]

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

    def _postprocess_image(self, image):
        image = image.crop(ImageOps.invert(image).getbbox())
        image = image.resize(SYMBOL_SIZE, resample=Image.BILINEAR)
        image = ImageOps.expand(image, SYMBOL_PADDING, (255, 255, 255))

        buf = BytesIO()
        image.save(buf, format='PNG')
        return b64encode(buf.getvalue())

    def _count_symbols(self):
        count = 0
        for command in self.commands:
            if command.code:
                count += 1
            for parameter in command.parameters:
                count += len(parameter)
        return count


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

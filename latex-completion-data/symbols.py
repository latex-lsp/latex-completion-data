from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
from typing import List, Dict, Optional
from util import with_progress
import util
import logging
import tex
import base64
import pdf2image
import multiprocessing


SYMBOL_SIZE = (48, 48)
SYMBOL_PADDING = 5


def load_unicode_symbols():
    file = Path(__file__).parent / 'data/unimathsymbols.txt'
    with file.open(encoding='utf-8') as f:
        lines = [l.strip().split('^') for l in f if not l.startswith('#')]
        symbols = {}
        for line in lines:
            candidates = (n[1:] for n in line if n.startswith('\\'))
            glyph = line[1]
            for cnd in candidates:
                symbols.setdefault(cnd, glyph)
        return symbols


UNICODE_SYMBOLS = load_unicode_symbols()


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
                  for img in pdf2image.convert_from_path(str(pdf_path), dpi=3000)]

        image_index = 0
        for cmd in self.commands:
            cmd_image = None
            if cmd.code:
                cmd_image = images[image_index]
                image_index += 1

            glyph = UNICODE_SYMBOLS.get(cmd.name)
            rendered_cmd = SymbolCommand(cmd.name, cmd_image, glyph)
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
        image.thumbnail(SYMBOL_SIZE, Image.BILINEAR)
        image = ImageOps.expand(image, SYMBOL_PADDING, (255, 255, 255))

        buf = BytesIO()
        image.save(buf, format='PNG')
        return str(b64encode(buf.getvalue()), encoding='utf-8')

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
        with ThreadPoolExecutor(multiprocessing.cpu_count()) as executor:
            task = with_progress('Rendering symbols', len(
                self.packages), UnrenderedSymbolPackage.render)
            return list(executor.map(task, self.packages))


SYMBOL_DATABASE = util.load_json('data/symbols.json', UnrenderedSymbolDatabase)


class SymbolCommandArgument:
    def __init__(self, name, image):
        self.name = name
        self.image = image


class SymbolCommand:
    def __init__(self, name, image, glyph=None):
        self.name = name
        self.image = image
        self.glyph = glyph
        self.parameters = []


class SymbolPackage:
    def __init__(self, name):
        self.name = name
        self.commands = []

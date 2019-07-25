from pathlib import Path
from enum import Enum
from tempfile import TemporaryDirectory
import subprocess
from subprocess import DEVNULL, TimeoutExpired
from dataclasses import dataclass
from typing import List
import util
import logging
from tqdm import tqdm


@dataclass
class Primitives:
    commands: List[str]
    environments: List[str]


KERNEL_PRIMITIVES = util.load_json('data/kernel.json', Primitives)


class Format(Enum):
    LATEX = 'latex'
    LUALATEX = 'lualatex'
    XELATEX = 'xelatex'

    @staticmethod
    def from_file(file):
        file = str(file)
        if "lua" in file:
            return Format.LUALATEX
        elif "xe" in file:
            return Format.XELATEX
        else:
            return Format.LATEX


class CompilationResult:
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def find(self, ext):
        return Path(self.tmpdir.name) / 'code.{}'.format(ext)

    def read_log(self):
        return self.find('log').read_text(errors='replace')


def compile(code, fmt=Format.LATEX, timeout=10, pdf=False):
    tmpdir = TemporaryDirectory()
    (Path(tmpdir.name) / 'code.tex').write_text(code)

    flags = ['-interaction=batchmode', '-shell-escape']
    if pdf:
        flags.append('-output-format=pdf')
    try:
        subprocess.run([fmt.value, *flags, 'code.tex'], cwd=tmpdir.name, timeout=timeout,
                       stdout=DEVNULL, stderr=DEVNULL)
        return CompilationResult(tmpdir)
    except TimeoutExpired as error:
        try:
            tmpdir.cleanup()
        except OSError:
            pass

        raise error


TEX_DIR_PATTERNS = ['tex/plain/**', 'tex/generic/**', 'tex/latex/**', 'tex/latex/pgf/**',
                    'tex/luatex/**', 'tex/lualatex/**', 'tex/xetex/**', 'tex/xelatex/**']


class FileResolver:
    def __init__(self):
        root_dir = self._find_root_dir()
        self.files_by_name = {x.name: x for x in self._read_database(root_dir)}

    def _find_root_dir(self):
        cmd = ['kpsewhich', '--var-value', 'TEXMFDIST']
        output = subprocess.run(cmd, capture_output=True, text=True).stdout
        return Path(output.splitlines()[0])

    def _read_database(self, root_dir):
        db_file = root_dir / 'ls-R'
        lines = list(x for x in db_file.read_text().splitlines()
                     if x and not x.isspace() and not x.startswith('%'))

        current_dir = None
        for line in tqdm(lines, desc='Loading resolver'):
            if line.endswith(':'):
                current_dir = root_dir / line[:-1]
            elif any(current_dir.match(pat) for pat in TEX_DIR_PATTERNS):
                file = current_dir / (line)
                if file.suffix:
                    yield file


FILE_RESOLVER = FileResolver()

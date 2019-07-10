
from pathlib import Path
from enum import Enum
from tempfile import TemporaryDirectory
import subprocess
from subprocess import DEVNULL, TimeoutExpired
from dataclasses import dataclass
from typing import List
import util


@dataclass
class Primitives:
    commands: List[str]
    environments: List[str]


KERNEL_PRIMITIVES = util.load_json('kernel.json', Primitives)


class Format(Enum):
    LATEX = 'latex'
    LUALATEX = 'lualatex'
    XELATEX = 'xelatex'


class CompilationResult:
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def find(self, ext):
        return Path(self.tmpdir.name) / 'code.{}'.format(ext)

    def find_img(self, index):
        return Path(self.tmpdir.name) / 'code{}.png'.format(index)

    def read_log(self):
        return self.find('log').read_text(errors='replace')


def compile(code, fmt=Format.LATEX, timeout=10):
    tmpdir = TemporaryDirectory()
    (Path(tmpdir.name) / 'code.tex').write_text(code)
    cmd = [fmt.value, '-interaction=batchmode',
           '-shell-escape', 'code.tex']
    try:
        subprocess.run(cmd, cwd=tmpdir.name, timeout=timeout,
                       stdout=DEVNULL, stderr=DEVNULL)
        return CompilationResult(tmpdir)
    except TimeoutExpired as error:
        tmpdir.cleanup()
        raise error


class FileResolver:
    def __init__(self):
        root_dir = self._find_root_dir()
        self.files_by_name = {x: x.name for x in self._read_database(root_dir)}

    def _find_root_dir(self):
        cmd = ['kpsewhich', '--var-value', 'TEXMFDIST']
        output = subprocess.run(cmd, capture_output=True, text=True).stdout
        return Path(output.splitlines()[0])

    def _read_database(self, root_dir):
        db_file = root_dir / 'ls-R'
        lines = (x for x in db_file.read_text().splitlines()
                 if x and not x.isspace() and not x.startswith('%'))

        current_dir = None
        for line in lines:
            if line.endswith(':'):
                current_dir = root_dir / line[:-1]
            else:
                file = current_dir.joinpath(line)
                if file.suffix:
                    yield file
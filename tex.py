import json
from pathlib import Path
from collections import namedtuple
from enum import Enum
from tempfile import TemporaryDirectory
import subprocess
from subprocess import DEVNULL, TimeoutExpired

KERNEL_PRIMITIVES = json.load((Path(__file__).parent / 'kernel.json').open(),
                              object_hook=lambda d: namedtuple('Primitives', d.keys())(*d.values()))


class Format(Enum):
    LATEX = 'latex'
    LUALATEX = 'lualatex'
    XELATEX = 'xelatex'


class CompilationResult:
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def find(self, ext):
        return Path(self.tmpdir.name) / 'code.{}'.format(ext)

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

import os
import tex
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from tarjan import tarjan
from subprocess import TimeoutExpired
from database import Component, Command
from util import with_progress
from pathlib import Path

FILE_REGEX = re.compile(r'\(([^\r\n()]+\.(sty|cls))')
CMD_REGEX = re.compile(r'^cmd:([a-zA-Z\*]+)$', re.MULTILINE)
COMPONENT_EXTS = ['.cls', '.sty']


class LatexPackage:
    def __init__(self, file, refs, cmds, envs):
        self.file = file
        self.refs = refs
        self.cmds = cmds
        self.envs = envs

    @staticmethod
    def load(file):
        code = LatexPackage._build_testcode(file)
        result = tex.compile(code, fmt=tex.Format.LUALATEX)

        log = result.read_log()
        includes = (Path(match[0]) for match in FILE_REGEX.findall(log))
        refs = [f for f in includes if f != file and f.name != 'minimal.cls']

        cmds = {match for match in CMD_REGEX.findall(log)}
        envs = {cmd for cmd in cmds if f'end{cmd}' in cmds}
        return LatexPackage(file, refs, cmds, envs)

    @staticmethod
    def _build_testcode(file):
        code = ''
        if file.suffix == '.cls':
            code += f'\\documentclass{{{file.stem}}}\n'
            code += r'''\directlua{
                            primitives = {}
                            for _, p in pairs(tex.primitives()) do
                                primitives[p] = true
                            end
                        }
                    '''
        else:
            code += '\\documentclass{minimal}\n'
            code += r'''\directlua{
                            primitives = {}
                            for _, p in pairs(tex.primitives()) do
                                primitives[p] = true
                            end

                            for _, v in pairs(tex.hashtokens()) do
                                local token = token.create(v)
                                if token then
                                    primitives[token.csname] = true
                                end
                            end
                        }
                    '''
            code += f'\\usepackage{{{file.stem}}}\n'
        code += r'''\begin{document}
                        \directlua{
                            for i, v in pairs(tex.hashtokens()) do
                                local token = token.create(v)
                                if token and not primitives[token.csname] then
                                    texio.write_nl("cmd:" .. token.csname)
                                end
                            end
                            texio.write_nl("")
                        }
                    \end{document}
                '''
        return code


def analyze(pkgs_by_name, file):
    pkgs_by_name[file.name] = LatexPackage(file, [], {}, {})
    try:
        pkgs_by_name[file.name] = LatexPackage.load(file)
    except TimeoutError:
        logging.warn(f'Could not analyze {file}.')


def generate_database():
    pkgs_by_name = {}
    files = [f for f in tex.FILE_RESOLVER.files_by_name.values()
             if f.suffix in COMPONENT_EXTS]

    with ThreadPoolExecutor(os.cpu_count()) as executor:
        task = with_progress('Indexing packages', len(
            files), partial(analyze, pkgs_by_name))
        executor.map(task, files)

    dep_graph = {pkg.file: [ref for ref in pkg.refs]
                 for pkg in pkgs_by_name.values()}

    components = []
    for component_files in tarjan(dep_graph):
        pkg = pkgs_by_name[component_files[0].name]
        names = [file.name for file in component_files]
        refs = [ref.name for ref in pkg.refs]

        for ref in (pkgs_by_name[ref.name] for ref in pkg.refs):
            pkg.cmds.difference_update(ref.cmds)
            pkg.envs.difference_update(ref.envs)
        pkg.cmds.difference_update(tex.KERNEL_PRIMITIVES.commands)
        pkg.envs.difference_update(tex.KERNEL_PRIMITIVES.environments)

        cmds = [Command(cmd) for cmd in sorted(pkg.cmds)]
        envs = sorted(pkg.envs)
        components.append(Component(names, refs, cmds, envs))
    return components

import tex
import re
import logging
from tarjan import tarjan
from subprocess import TimeoutExpired
from tqdm import tqdm
from appendix import APPENDIX

FILE_REGEX = re.compile(r'[^\s\r\n]+\.(?:sty|tex|def|cls)')
PRIMITIVE_REGEX = re.compile(r'[a-zA-Z]+')
COMPONENT_EXTS = ['.cls', '.sty']


class LatexDependency:
    def __init__(self, file):
        self.file = file
        try:
            self.includes = self._find_includes(file)
        except:
            self.includes = [file]

    def __str__(self):
        return self.file.__str__()

    def references(self):
        return [inc for inc in self.includes if inc != self.file and inc.suffix in COMPONENT_EXTS]

    def load_components(self, components_by_name):
        missing_deps = {ref: LatexDependency(ref)
                        for ref in self.references() if ref.name not in components_by_name}
        missing_deps[self.file] = self

        graph = {dep: [missing_deps[ref] for ref in dep.references() if ref in missing_deps]
                 for dep in missing_deps.values()}
        return tarjan(graph)

    @staticmethod
    def _find_includes(file):
        code = _build_testcode_header(file)
        code += '''
            \\listfiles
            \\begin{document}
            \\end{document}'''
        result = tex.compile(code, fmt=tex.Format.from_file(file))
        log = result.read_log()
        start_index = log.index('*File List*')
        file_names = re.findall(FILE_REGEX, log[start_index:])
        return [tex.FILE_RESOLVER.files_by_name[name]
                for name in file_names if name.endswith('.cls') or name != 'article.cls']


class LatexComponent:
    def __init__(self, component, loaded_refs):
        dependency = component[0]
        candidates = self._find_likely_primitives(dependency, loaded_refs)
        self.commands, self.environments = self.check_primitives(
            dependency.file, candidates)
        self.file_names = [dep.file.name for dep in component]
        self.references = [file.name for dep in component
                           for file in dep.references()]

    @staticmethod
    def _find_likely_primitives(dependency, loaded_refs):
        code = dependency.file.read_text(errors='ignore')
        for include in dependency.includes:
            code += include.read_text(errors='ignore')

        likely_primitives = set(re.findall(PRIMITIVE_REGEX, code))
        likely_primitives.difference_update(tex.KERNEL_PRIMITIVES.commands)
        likely_primitives.difference_update(tex.KERNEL_PRIMITIVES.environments)
        likely_primitives.difference_update(
            {cmd for ref in loaded_refs for cmd in ref.commands})
        likely_primitives.difference_update(
            {env for ref in loaded_refs for env in ref.environments})
        return likely_primitives

    @staticmethod
    def check_primitives(file, candidates):
        code = _build_testcode_header(file)
        code += '\\makeatletter\n'
        code += '\\begin{document}\n'
        for candidate in candidates:
            code += f'''
                \\@ifundefined{{{candidate}}}{{ }}
                {{
                    \\@ifundefined{{end{candidate}}}
                    {{
                        \\wlog{{cmd:{candidate}}}
                    }}
                    {{
                        \\wlog{{env:{candidate}}}
                    }}
                }}'''
        code += '\\end{document}'

        result = tex.compile(code, fmt=tex.Format.from_file(file))
        lines = result.read_log().splitlines()

        cmds = [x.split(':')[1] for x in lines if x.startswith('cmd:')]
        envs = [x.split(':')[1] for x in lines if x.startswith('env:')]
        return cmds, envs


def _build_testcode_header(file):
    code = ''
    if file.suffix == '.cls':
        code += f'\\documentclass{{{file.stem}}}\n'
    else:
        code += '\\documentclass{article}\n'
        code += f'\\usepackage{{{file.stem}}}\n'
    return code


def analyze(file, components_by_name):
    for component in LatexDependency(file).load_components(components_by_name):
        dependency = component[0]
        loaded_refs = [components_by_name[ref.name]
                       for ref in dependency.references() if ref.name in components_by_name]
        try:
            component = LatexComponent(component, loaded_refs)
            for name in component.file_names:
                components_by_name[name] = component
        except TimeoutExpired:
            logging.warn(f'Could not analyze {file}.')


def include_appendix(components_by_name):
    for src_component in APPENDIX.components:
        dst_component = components_by_name[src_component.name]
        dst_component.commands.extend(src_component.commands)
        dst_component.commands = list(dict.fromkeys(dst_component.commands))
        dst_component.environments.extend(src_component.environments)
        dst_component.environments = list(
            dict.fromkeys(dst_component.environments))
    pass


def generate_database():
    components_by_name = {}
    for name, file in tqdm(tex.FILE_RESOLVER.files_by_name.items(), desc='Indexing packages'):
        if file.suffix in COMPONENT_EXTS and name not in components_by_name:
            analyze(file, components_by_name)
    include_appendix(components_by_name)
    return components_by_name.values()

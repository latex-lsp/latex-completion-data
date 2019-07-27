from pathlib import Path
from jsons import KEY_TRANSFORMER_CAMELCASE
import logging
import symbols
import tex
import util
import components
import metadata
import os
import jsons


class Database:
    def __init__(self):
        self.components = []
        self.metadata = []

    def find_package(self, name):
        for component in self.components:
            if name:
                file_name = name + '.sty'
                if file_name in component.file_names:
                    return component
            else:
                if component.file_names == []:
                    return component


class Component:
    def __init__(self, file_names, references, commands, environments):
        self.file_names = file_names
        self.references = references
        self.commands = commands
        self.environments = environments
        pass


class Command:
    def __init__(self, name):
        self.name = name
        self.image = None
        self.parameters = []
        pass


class Metadata:
    def __init__(self, name, caption, description):
        self.name = name
        self.caption = caption
        self.description = description


def main():
    logging.basicConfig(format='%(levelname)-8s %(message)s',
                        level=logging.INFO, filename='latex-completion-data.log', filemode='w')

    database = Database()
    database.components.append(Component([], [],
                                         [Command(x)
                                          for x in tex.KERNEL_PRIMITIVES.commands],
                                         tex.KERNEL_PRIMITIVES.environments))

    for component in components.generate_database():
        commands = [Command(name) for name in component.commands]
        database.components.append(Component(component.file_names, component.references,
                                             commands, component.environments))

    for src_package in symbols.SYMBOL_DATABASE.render():
        dst_package = database.find_package(src_package.name)
        if dst_package is None:
            logging.error(
                f'Package {src_package.name} was not indexed but has symbols')
            continue

        for src_command in src_package.commands:
            for dst_command in dst_package.commands:
                if src_command.name == dst_command.name:
                    dst_command.image = src_command.image
                    dst_command.parameters = src_command.parameters

    database.metadata = metadata.extract()
    json = jsons.dumps(database, key_transformer=KEY_TRANSFORMER_CAMELCASE)
    path = Path(os.getcwd()) / 'completion.json'
    path.write_text(json)


if __name__ == '__main__':
    main()

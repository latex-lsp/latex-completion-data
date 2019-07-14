import logging
from timeit import default_timer as timer
import symbols
import tex
import util
import components


class Database:
    def __init__(self):
        self.components = []

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


def main():
    logging.basicConfig(format='%(levelname)-8s %(message)s',
                        level=logging.INFO, filename='latex-completion-data.log', filemode='w')

    start_time = timer()
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
        for src_command in src_package.commands:
            for dst_command in dst_package.commands:
                if src_command.name == dst_command.name:
                    dst_command.image = src_command.image
                    dst_command.parameters = src_command.parameters

    util.save_json('completion.json', database)
    end_time = timer()
    logging.info('Elapsed time: %d seconds', end_time - start_time)


if __name__ == '__main__':
    main()

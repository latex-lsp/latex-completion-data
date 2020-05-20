from pathlib import Path
from jsons import KEY_TRANSFORMER_CAMELCASE
from database import Database, Command, Component
import logging
import symbols
import tex
import util
import components
import metadata
import os
import jsons


def main():
    logging.basicConfig(format='%(levelname)-8s %(message)s',
                        level=logging.INFO, filename='latex-completion-data.log', filemode='w')

    database = Database()
    database.components = components.generate_database()
    database.components.append(Component([], [],
                                         [Command(x)
                                          for x in tex.KERNEL_PRIMITIVES.commands],
                                         tex.KERNEL_PRIMITIVES.environments))

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
                    dst_command.glyph = src_command.glyph
                    dst_command.parameters = src_command.parameters

    database.metadata = metadata.extract()
    json = jsons.dumps(database, key_transformer=KEY_TRANSFORMER_CAMELCASE)
    path = Path(os.getcwd()) / 'completion.json'
    path.write_text(json)
    print()


if __name__ == '__main__':
    main()

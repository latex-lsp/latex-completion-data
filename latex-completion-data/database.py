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
        self.glyph = None
        self.parameters = []
        pass


class Metadata:
    def __init__(self, name, caption, description):
        self.name = name
        self.caption = caption
        self.description = description

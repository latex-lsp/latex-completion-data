from dataclasses import dataclass
import util
from typing import List, Dict


@dataclass
class SymbolCommandArgument:
    name: str
    code: str


@dataclass
class SymbolCommand:
    name: str
    code: str
    arguments: List[List[SymbolCommandArgument]]


@dataclass
class SymbolPackage:
    name: str
    font_encoding: str
    commands: List[SymbolCommand]


@dataclass
class SymbolDatabase:
    packages: List[SymbolPackage]


SYMBOL_DATABASE = util.load_json('symbols.json', SymbolDatabase)

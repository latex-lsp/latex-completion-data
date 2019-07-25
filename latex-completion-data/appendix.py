from dataclasses import dataclass
import util
from typing import List, Dict, Optional


@dataclass
class AppendixComponent:
    name: str
    commands: List[str]
    environments: List[str]


@dataclass
class Appendix:
    components: List[AppendixComponent]
    pass


APPENDIX = util.load_json('data/appendix.json', Appendix)

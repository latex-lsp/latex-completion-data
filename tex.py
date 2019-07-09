import json
from pathlib import Path
from collections import namedtuple

KERNEL_PRIMITIVES = json.load((Path(__file__).parent / 'kernel.json').open(),
                              object_hook=lambda d: namedtuple('Primitives', d.keys())(*d.values()))

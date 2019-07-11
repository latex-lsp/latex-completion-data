import jsons
from pathlib import Path


def load_json(name, cls):
    path = Path(__file__).parent / name
    json = path.read_text()
    return jsons.loads(json, cls, key_transformer=jsons.KEY_TRANSFORMER_SNAKECASE)


def save_json(name, obj):
    path = Path(__file__).parent / name
    json = jsons.dumps(obj, key_transformer=jsons.KEY_TRANSFORMER_CAMELCASE)
    path.write_text(json)

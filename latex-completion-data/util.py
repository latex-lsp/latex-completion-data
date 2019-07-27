import jsons
from pathlib import Path
from tqdm import tqdm


def load_json(name, cls):
    path = Path(__file__).parent / name
    json = path.read_text()
    return jsons.loads(json, cls, key_transformer=jsons.KEY_TRANSFORMER_SNAKECASE)


def with_progress(desc, total, f):
    pbar = tqdm(desc=desc, total=total)

    def do_work(arg):
        result = f(arg)
        pbar.update()
        return result

    return do_work

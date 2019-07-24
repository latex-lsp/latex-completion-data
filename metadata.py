from dataclasses import dataclass
from typing import List, Optional, Any, Union
from tqdm import tqdm
from main import Metadata
import concurrent.futures
import requests
import jsons
import pypandoc


@dataclass
class Description:
    language: Optional[str]
    text: str


@dataclass
class Response:
    name: str
    caption: str
    descriptions: List[Description]


@dataclass
class Error:
    errors: Any


def query_package_list():
    packages = requests.get('https://ctan.org/json/2.0/packages').json()
    return list(map(lambda pkg: pkg['key'], packages))


def query(name):
    json = requests.get(f'http://ctan.org/json/2.0/pkg/{name}').text
    response = jsons.loads(
        json, Union[Response, Error], key_transformer=jsons.KEY_TRANSFORMER_SNAKECASE)

    if isinstance(response, Error):
        return None

    html = next(
        (d.text for d in response.descriptions if not d.language), '')
    description = pypandoc.convert_text(html, 'markdown', format='html')

    return Metadata(name, response.caption, description)


def query_all():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        packages = query_package_list()
        metadata = tqdm(executor.map(query, packages),
                        desc='Querying metadata', total=len(packages))
        return list(filter(None, metadata))

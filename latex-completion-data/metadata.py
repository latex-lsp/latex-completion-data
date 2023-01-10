from database import Metadata
from pathlib import Path
from components import COMPONENT_EXTS
from tqdm import tqdm
import requests
import tlpdb
from tex import find_root_dir


def is_valid_package(package):
    return not package.name.startswith('00') and package.shortdesc and package.longdesc


def extract():
    lines = open(find_root_dir().parent.as_posix() + "/tlpkg/texlive.tlpdb").readlines()
    packages, _ = tlpdb.packages_from_tlpdb(lines)

    metadata = []
    for package in tqdm(filter(is_valid_package, packages), desc='Extracting metadata'):
        caption = package.shortdesc.strip()
        description = package.longdesc.strip()

        files = [Path(file) for file in package.runfiles]
        for file in (f for f in files if f.suffix in COMPONENT_EXTS):
            metadata.append(Metadata(file.stem, caption, description))

    return metadata

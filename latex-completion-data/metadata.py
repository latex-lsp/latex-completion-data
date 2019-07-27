from main import Metadata
from pathlib import Path
from components import COMPONENT_EXTS
from tqdm import tqdm
import requests
import tlpdb


TEXLIVE_TLPDB_URL = 'http://mirror.ctan.org/tex-archive/systems/texlive/tlnet/tlpkg/texlive.tlpdb'


def extract():
    lines = requests.get(TEXLIVE_TLPDB_URL).text.splitlines()
    packages, _ = tlpdb.packages_from_tlpdb(lines)

    metadata = []
    for package in tqdm(packages, desc='Extracting metadata'):
        if package.name.startswith('00'):
            continue

        for file in package.runfiles:
            file = Path(file)
            if file.suffix in COMPONENT_EXTS:
                metadata.append(
                    Metadata(file.stem, package.shortdesc, package.longdesc))
                    
    return metadata

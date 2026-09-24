"""Copy the five Northwind inputs from the supplied project folder, verifying existing copies."""
import argparse
import hashlib
import shutil
from pathlib import Path
from northwind_lakehouse import FILES

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('project_dir', type=Path)
args = parser.parse_args()
source = args.project_dir / 'northwind_thai_large_data'
if not source.is_dir():
    source = args.project_dir / 'project' / 'northwind_thai_large_data'
target = Path(__file__).resolve().parents[1] / 'data/landing/northwind_thai_large_data'
for name in FILES:
    src, dst = source / name, target / name
    if not src.is_file():
        raise FileNotFoundError(src)
    if dst.exists() and hashlib.sha256(src.read_bytes()).digest() != hashlib.sha256(dst.read_bytes()).digest():
        raise FileExistsError(f'Existing file differs; review before replacing: {dst}')
target.mkdir(parents=True, exist_ok=True)
for name in FILES:
    dst = target / name
    if not dst.exists():
        shutil.copy2(source / name, dst)
    print(f'Verified: {name}')

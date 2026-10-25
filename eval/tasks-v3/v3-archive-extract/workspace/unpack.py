from pathlib import Path
import tarfile
from typing import BinaryIO

def extract(source: BinaryIO, destination: str | Path, *, max_files: int, max_bytes: int, dry_run: bool = False) -> dict:
    with tarfile.open(fileobj=source, mode='r|*') as archive:
        files = [m for m in archive if m.isfile()]
    return {'files': len(files), 'bytes': sum(m.size for m in files), 'paths': sorted(m.name for m in files)}

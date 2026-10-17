"""Shared filesystem controls and machine-readable results."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

class GateError(ValueError):
    pass

def workspace_root() -> Path:
    value = os.environ.get('CODEVIDEO_WORKSPACE')
    if not value:
        raise GateError('CODEVIDEO_WORKSPACE is unset. Configure an absolute, dedicated project root.')
    root = Path(value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise GateError('CODEVIDEO_WORKSPACE must be a directory.')
    if root == Path('/') or str(root) == str(Path.home()):
        raise GateError('Refusing broad workspace root; use a dedicated project folder.')
    return root

def inside(root: Path, path: str | Path, *, must_exist: bool = False) -> Path:
    """Constrain path to root even if caller supplies .. or a symlink."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = root / p
    resolved = p.resolve(strict=must_exist)
    try:
        resolved.relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise GateError('Path outside CODEVIDEO_WORKSPACE refused') from exc
    return resolved

def slug(name: str) -> str:
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,49}', name):
        raise GateError('ID must be 1-50 ASCII letters, numbers, underscores or dashes.')
    return name

def load_json(path: Path) -> dict:
    with path.open(encoding='utf-8') as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise GateError('Expected a JSON object')
    return obj

def save_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n'
    fd, temp = tempfile.mkstemp(prefix='.cv-', suffix='.json', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def stable_hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def tool(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise GateError(f'Required executable not found: {name}')
    return binary

def result(status: str, **kwargs) -> dict:
    return {'status': status, **kwargs}

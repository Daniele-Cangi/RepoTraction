"""Small, allowlisted local configuration reader; never executes dotenv content."""
from pathlib import Path
import os
import re


def provider_environment(path=None):
    path = Path(path) if path is not None else Path(__file__).resolve().parents[1] / ".env"
    values = {}
    if path.exists():
        if path.is_symlink() or path.stat().st_size > 16384:
            raise ValueError("Local provider configuration must be a regular file of at most 16 KB.")
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not separator or not re.fullmatch(r"REPOTRACTION_AI_[A-Z_]+", key):
                raise ValueError("Local provider configuration contains an unsupported assignment.")
            if key in values:
                raise ValueError("Local provider configuration contains a duplicate assignment.")
            if value.startswith(("'", '"')):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError("Local provider configuration contains an unclosed quote.")
                value = value[1:-1]
            if any(ord(char) < 32 for char in value):
                raise ValueError("Local provider configuration contains control characters.")
            values[key] = value
    # Explicit process configuration wins. Neither interpolation nor shell syntax is evaluated.
    values.update({key: value for key, value in os.environ.items() if key.startswith("REPOTRACTION_AI_")})
    return values

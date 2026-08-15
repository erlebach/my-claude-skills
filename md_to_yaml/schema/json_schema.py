"""JSON Schema export utility for the slide DSL.

Generates JSON Schema from the Deck Pydantic model and writes it to disk.
"""
from __future__ import annotations

import json
from pathlib import Path

from schema.models import Deck


def generate_schema() -> dict:
    """Generate JSON Schema from the Deck Pydantic model."""
    return Deck.model_json_schema()


def write_schema(output_path: str | Path | None = None) -> Path:
    """Write JSON Schema to file.

    Args:
        output_path: Destination path. Defaults to schema/deck.schema.json
                     (sibling to this file).

    Returns:
        Resolved Path where the schema was written.
    """
    if output_path is None:
        output_path = Path(__file__).parent / 'deck.schema.json'
    output_path = Path(output_path)
    schema = generate_schema()
    output_path.write_text(json.dumps(schema, indent=2) + '\n', encoding='utf-8')
    return output_path


if __name__ == '__main__':
    path = write_schema()
    print(f'Schema written to {path}')

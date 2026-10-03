"""Write the OpenAPI document to a file. Used by the frontend's `npm run gen:api`."""

import json
import sys
from pathlib import Path

from app.main import app


def write_spec(destination: Path) -> None:
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(app.openapi(), indent=2) + "\n")


def main(argv: list[str]) -> None:
    write_spec(Path(argv[1] if len(argv) > 1 else "openapi.json"))


if __name__ == "__main__":
    main(sys.argv)

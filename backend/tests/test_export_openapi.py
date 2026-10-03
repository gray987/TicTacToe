import json
from pathlib import Path

from app.export_openapi import write_spec


def test_write_spec_writes_a_valid_openapi_document(tmp_path: Path) -> None:
    destination = tmp_path / "openapi.json"
    write_spec(destination)
    spec = json.loads(destination.read_text(encoding="utf-8"))
    assert spec["openapi"].startswith("3.")
    assert "/api/v1/games" in spec["paths"]
    assert "ErrorResponse" in spec["components"]["schemas"]

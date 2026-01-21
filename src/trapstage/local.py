import json
from pathlib import Path

j = json.loads(Path(Path(__file__).parent / "trapsformat.json").read_text(encoding="utf-8"))

for k, v in j.items():
    j[k]["settings"] = {}

Path(Path(__file__).parent / "trapsformat.json").write_text(json.dumps(j, ensure_ascii=False, indent=4), encoding="utf-8")
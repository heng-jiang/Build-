#!/usr/bin/env python3
"""Package the XBuilder project and embed its assets in the offline preview."""

import base64
import json
from pathlib import Path
import struct
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "project"
DIST = ROOT / "dist"


def validate_project():
    config = json.loads((PROJECT / "assets/index.json").read_text())
    assert config["run"] == {"width": 480, "height": 360}
    for path in PROJECT.rglob("*.json"):
        data = json.loads(path.read_text())
        for costume in data.get("costumes", data.get("backdrops", [])):
            image = path.parent / costume["path"]
            assert image.is_file(), image
            if image.suffix == ".png":
                contents = image.read_bytes()
                assert contents[:8] == b"\x89PNG\r\n\x1a\n", image
                dimensions = struct.unpack(">II", contents[16:24])
                assert dimensions == (
                    costume["imageWidth"], costume["imageHeight"]
                ), image


def archive(path, include_readme):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        for file in sorted(PROJECT.rglob("*")):
            if file.is_file() and (include_readme or file.name != "README.txt"):
                package.write(file, file.relative_to(PROJECT))


def preview():
    paths = {
        "sky": "assets/sky.png",
        "far": "assets/sprites/FarMeadow/far.png",
        "track": "assets/sprites/Track/track.png",
        "ball": "assets/sprites/CaptureBall0/capture-ball.png",
        "orb": "assets/sprites/EnergyOrb0/energy-orb.png",
    }
    paths.update({f"run{i}": f"assets/sprites/Pikachu/run{i}.png" for i in range(6)})
    paths.update({f"glow{i}": f"assets/sprites/DashFX/glow{i}.png" for i in range(2)})
    assets = {
        name: "data:image/png;base64,"
        + base64.b64encode((PROJECT / path).read_bytes()).decode("ascii")
        for name, path in paths.items()
    }
    template = (ROOT / "web/index.template.html").read_text()
    assert template.count("__ASSETS__") == 1
    (ROOT / "index.html").write_text(template.replace("__ASSETS__", json.dumps(assets)))


if __name__ == "__main__":
    validate_project()
    DIST.mkdir(exist_ok=True)
    archive(DIST / "pikachu-electric-v6.xbp", include_readme=False)
    archive(DIST / "pikachu-electric-v6-source.zip", include_readme=True)
    preview()
    print("Built v6 XBuilder project, source ZIP, and offline index.html")

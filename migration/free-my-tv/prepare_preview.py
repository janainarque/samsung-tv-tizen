"""Prepare browser files only: no WGT, SDK, signing, configuration secrets or TV access."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import webapp


def main():
    # Reuse upstream generation with its generic defaults, without reading config.properties.
    files = webapp.files(dict(webapp.GENERIC), "prepare_preview.py")
    for name in ("LICENSE", "UPSTREAM_README.md"):
        files[name] = (ROOT / name).read_bytes()
    output = ROOT / "preview"
    # No recursive cleanup: regenerate the known files in this isolated directory only.
    for name, content in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    print("Browser preview: " + str(output / "index.html"))
    print("No TV package generated. No signing or installation performed.")


if __name__ == "__main__":
    main()

"""SoundFont download utility."""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_URLS = [
    "https://github.com/FluidSynth/fluidsynth/releases/download/v2.3.4/FluidR3_GM.sf2",
    "https://musical-artifacts.com/artifacts/516/FluidR3_GM.sf2",
]

DEFAULT_DEST = "data/soundfonts"
KNOWN_HASH = None  # We skip hash verification for simplicity


def download_soundfont(
    url: Optional[str] = None,
    dest_dir: Optional[str] = None,
    filename: str = "FluidR3_GM.sf2",
) -> dict:
    """Download a SoundFont file. Tries multiple URLs. Returns {path, success, message}."""
    dest = Path(dest_dir or DEFAULT_DEST)
    dest.mkdir(parents=True, exist_ok=True)
    dest_path = dest / filename

    if dest_path.exists():
        return {"success": True, "path": str(dest_path), "message": "Already exists", "downloaded": False}

    urls = [url] if url else DEFAULT_URLS
    import urllib.request

    for u in urls:
        try:
            logger.info(f"Downloading SoundFont from {u} ...")
            req = urllib.request.Request(u, headers={"User-Agent": "CantioDAW/0.1"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            dest_path.write_bytes(data)
            size_mb = len(data) / (1024 * 1024)
            return {
                "success": True,
                "path": str(dest_path),
                "message": f"Downloaded {size_mb:.1f} MB",
                "url": u,
                "downloaded": True,
            }
        except Exception as e:
            logger.warning(f"Failed to download from {u}: {e}")
            continue

    return {
        "success": False,
        "path": str(dest_path),
        "message": "Failed to download from all URLs. Place a .sf2 file manually in data/soundfonts/",
        "downloaded": False,
    }


def ensure_soundfont_available(soundfont_path: Optional[str] = None) -> Optional[str]:
    """Ensure a SoundFont is available. Returns path or None."""
    if soundfont_path and os.path.isfile(soundfont_path):
        return soundfont_path

    from cantiodaw.synthesis.soundfont import _find_sf2_paths
    sf2_files = _find_sf2_paths()
    if sf2_files:
        return str(sf2_files[0])

    result = download_soundfont()
    if result["success"]:
        return result["path"]

    return None

"""
Download and prepare training data.

Debris class  -> gonzz2026/A-dataset-of-images-of-floating-rubbish-on-the-surface-of-the-water
                 (HuggingFace, zip, 2377 real photos of rubbish on water)
               + OceanCV/PlasticInWater repo jpg files (300 webcam images, tank plastic)
Clean class   -> Wikimedia Commons full-text image search (CC-BY / CC0 ocean/sea photos)

Usage:
    cd PlasticPatrol
    python -m ml_classifier.data_prep --out_dir ./data
"""

import argparse
import io
import os
import time
import zipfile

import requests


def _save_bytes(img_bytes: bytes, path: str) -> None:
    with open(path, "wb") as f:
        f.write(img_bytes)


# ---------------------------------------------------------------------------
# Debris — gonzz2026 floating rubbish zip
# ---------------------------------------------------------------------------

def extract_gonzz_debris(out_dir: str, max_images: int = 1000) -> int:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise RuntimeError("pip install huggingface_hub")

    debris_dir = os.path.join(out_dir, "debris")
    os.makedirs(debris_dir, exist_ok=True)

    print("Downloading gonzz2026 floating-rubbish dataset…")
    zip_path = hf_hub_download(
        repo_id="gonzz2026/A-dataset-of-images-of-floating-rubbish-on-the-surface-of-the-water",
        filename="A-dataset-of-images-of-floating-rubbish-on-the-surface-of-the-water.zip",
        repo_type="dataset",
    )

    saved = 0
    with zipfile.ZipFile(zip_path) as z:
        img_names = [n for n in z.namelist() if n.lower().endswith((".jpg", ".jpeg", ".png"))]
        for name in img_names:
            if saved >= max_images:
                break
            dest = os.path.join(debris_dir, f"rubbish_{saved:05d}.jpg")
            data = z.read(name)
            _save_bytes(data, dest)
            saved += 1
            print(f"\r  debris (gonzz) {saved}/{min(max_images, len(img_names))}", end="", flush=True)

    print(f"\n  Saved {saved} images → {debris_dir}")
    return saved


# ---------------------------------------------------------------------------
# Debris — OceanCV/PlasticInWater repo direct jpg files
# ---------------------------------------------------------------------------

def download_oceancv_debris(out_dir: str, max_images: int = 300) -> int:
    try:
        from huggingface_hub import hf_hub_download, list_repo_files
    except ImportError:
        raise RuntimeError("pip install huggingface_hub")

    debris_dir = os.path.join(out_dir, "debris")
    os.makedirs(debris_dir, exist_ok=True)

    print("Fetching OceanCV/PlasticInWater image list…")
    all_files = list(list_repo_files("OceanCV/PlasticInWater", repo_type="dataset"))
    jpg_files = [f for f in all_files if f.lower().endswith((".jpg", ".jpeg"))][:max_images]

    saved = 0
    existing = len([f for f in os.listdir(debris_dir) if f.startswith("rubbish_")])

    for file_path in jpg_files:
        local = hf_hub_download(
            repo_id="OceanCV/PlasticInWater",
            filename=file_path,
            repo_type="dataset",
        )
        dest = os.path.join(debris_dir, f"oceancv_{saved:05d}.jpg")
        with open(local, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
        saved += 1
        print(f"\r  debris (oceancv) {saved}/{len(jpg_files)}", end="", flush=True)

    print(f"\n  Saved {saved} images → {debris_dir}")
    return saved


# ---------------------------------------------------------------------------
# Clean water — Wikimedia Commons full-text image search
# ---------------------------------------------------------------------------

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
_HEADERS = {"User-Agent": "PlasticPatrolBot/1.0 (research project, contact: admin@plasticpatrol.org)"}

SEARCH_TERMS = [
    "ocean water surface blue",
    "sea water surface clear",
    "clean ocean waves",
    "blue ocean sea surface",
    "mediterranean sea water",
    "tropical ocean surface",
    "clear blue sea water",
    "open ocean blue water",
    "calm sea surface",
    "pacific ocean water",
]


def _wikimedia_search_images(query: str, limit: int = 50) -> list[dict]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|mediatype|size",
        "iiurlwidth": "640",
        "format": "json",
    }
    try:
        r = requests.get(WIKIMEDIA_API, params=params, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            url = info.get("thumburl") or info.get("url", "")
            # Skip very small images and non-photos
            if url and info.get("mediatype") in ("BITMAP", None):
                results.append({"title": page.get("title", ""), "url": url})
        return results
    except Exception:
        return []


def download_clean(out_dir: str, max_images: int = 400) -> int:
    clean_dir = os.path.join(out_dir, "clean")
    os.makedirs(clean_dir, exist_ok=True)

    collected: dict[str, str] = {}
    print("Searching Wikimedia Commons for clean ocean water images…")
    for term in SEARCH_TERMS:
        results = _wikimedia_search_images(term, limit=50)
        for r in results:
            collected[r["title"]] = r["url"]
        print(f"  '{term}' → {len(results)} results (total unique: {len(collected)})")
        if len(collected) >= max_images * 2:
            break

    session = requests.Session()
    session.headers.update(_HEADERS)

    saved = 0
    fails = 0
    for title, url in list(collected.items()):
        if saved >= max_images:
            break
        try:
            resp = session.get(url, timeout=25)
            if resp.status_code == 429:
                time.sleep(5)
                resp = session.get(url, timeout=25)
            resp.raise_for_status()
            if len(resp.content) < 10_000:  # skip tiny/broken images
                continue
            dest = os.path.join(clean_dir, f"clean_{saved:05d}.jpg")
            _save_bytes(resp.content, dest)
            saved += 1
            fails = 0
            print(f"\r  clean {saved}/{max_images}", end="", flush=True)
        except Exception:
            fails += 1
            continue

    print(f"\n  Saved {saved} clean images → {clean_dir}")
    return saved


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", default="./data")
    parser.add_argument("--debris_count", type=int, default=800)
    parser.add_argument("--clean_count", type=int, default=400)
    parser.add_argument("--skip_oceancv", action="store_true", help="Skip OceanCV download (slow)")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    print(f"Output: {os.path.abspath(args.out_dir)}\n")

    d = extract_gonzz_debris(args.out_dir, max_images=args.debris_count)
    if not args.skip_oceancv:
        d += download_oceancv_debris(args.out_dir, max_images=100)
    c = download_clean(args.out_dir, max_images=args.clean_count)

    print(f"\nDataset ready: {d} debris + {c} clean images")
    print(f"Train with:\n  python -m ml_classifier.train --data_dir {args.out_dir}")


if __name__ == "__main__":
    main()

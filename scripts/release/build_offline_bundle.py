#!/usr/bin/env python3
"""
Build an offline-ready Satya bundle for low-spec (4GB RAM, CPU-only) devices.

Outputs:
- dist/offline_bundle/ (ready-to-ship directory)
- dist/offline_bundle.zip (compressed archive)
"""

import argparse
import shutil
import sys
from pathlib import Path


def copy_optional(src: Path, dest: Path) -> None:
    """Copy a file or directory if it exists."""
    if not src.exists():
        return
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def build_bundle(base_dir: Path, output_dir: Path) -> Path:
    """Create the offline bundle directory and zip archive."""
    bundle_dir = output_dir / "offline_bundle"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Paths to include
    includes = {
        "satya_data/models": base_dir / "satya_data" / "models",
        "satya_data/chroma_db": base_dir / "satya_data" / "chroma_db",
        "satya_data/content": base_dir / "satya_data" / "content",
        "docs": base_dir / "docs",
        "scripts/release": base_dir / "scripts" / "release",
        "requirements.txt": base_dir / "requirements.txt",
    }

    for rel, src in includes.items():
        copy_optional(src, bundle_dir / rel)

    # Zip it for transport
    archive_path = output_dir / "offline_bundle"
    shutil.make_archive(str(archive_path), "zip", root_dir=bundle_dir)
    return bundle_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build offline Satya bundle.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root (auto-detected).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "dist",
        help="Output directory for the bundle.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = build_bundle(args.base_dir, args.output_dir)
    print(f"Offline bundle created at: {bundle_dir}")
    print(f"Archive: {args.output_dir / 'offline_bundle.zip'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


"""
Download a subset of the GitLab Handbook and organise it by department.

Usage:
    python scripts/download_handbook.py                 # default: 100 pages/department
    python scripts/download_handbook.py --max-per-dept 60
    python scripts/download_handbook.py --list-folders  # see what exists in the repo

Output: data/raw/<department>/<file>.md
"""
import os
import stat


def _force_remove(func, path, *_):
    """Windows: git marks pack files read-only. Clear the flag, then retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def safe_rmtree(path, ignore_errors=False):
    if not Path(path).exists():
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force_remove, ignore_errors=ignore_errors)
    else:
        shutil.rmtree(path, onerror=_force_remove, ignore_errors=ignore_errors)
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://gitlab.com/gitlab-com/content-sites/handbook.git"
CLONE_DIR = Path(".handbook_clone")
CONTENT_ROOT = "content/handbook"
OUT_DIR = Path("data/raw")

# Handbook folder  ->  department in our app
# If a folder name doesn't exist, the script skips it. Run --list-folders to check.
DEPARTMENT_MAP = {
    "people-group": "hr",
    "engineering": "engineering",
    "security": "security",
    "finance": "finance",
    "company": "general",
    "values": "general",
    "communication": "general",
    "people-policies": "hr",
    "total-rewards": "hr",
    "legal": "general",
}


def run(cmd, cwd=None):
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def sparse_clone(folders):
    if CLONE_DIR.exists():
        safe_rmtree(CLONE_DIR)
    run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
         REPO_URL, str(CLONE_DIR)])
    paths = [f"{CONTENT_ROOT}/{f}" for f in folders]
    run(["git", "sparse-checkout", "set", *paths], cwd=CLONE_DIR)


def list_folders():
    if CLONE_DIR.exists():
        safe_rmtree(CLONE_DIR)
    run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
         REPO_URL, str(CLONE_DIR)])
    run(["git", "sparse-checkout", "set", CONTENT_ROOT], cwd=CLONE_DIR)
    root = CLONE_DIR / CONTENT_ROOT
    print("\nTop-level handbook folders:")
    for p in sorted(root.iterdir()):
        if p.is_dir():
            print("  -", p.name)
    safe_rmtree(CLONE_DIR)


def collect(max_per_dept):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    counts = {}
    for folder, dept in DEPARTMENT_MAP.items():
        src = CLONE_DIR / CONTENT_ROOT / folder
        if not src.exists():
            print(f"[skip] folder not found: {folder}")
            continue
        dest = OUT_DIR / dept
        dest.mkdir(parents=True, exist_ok=True)
        # Prefer larger files (more content), skip tiny stubs
        files = [f for f in src.rglob("*.md") if f.stat().st_size > 800]
        files.sort(key=lambda f: f.stat().st_size, reverse=True)
        already = counts.get(dept, 0)
        for f in files:
            if already >= max_per_dept:
                break
            rel = f.relative_to(src)
            # flatten path into a unique filename: sub/dir/page.md -> folder__sub__dir__page.md
            name = f"{folder}__" + "__".join(rel.parts)
            shutil.copy(f, dest / name)
            already += 1
        counts[dept] = already
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-dept", type=int, default=100)
    ap.add_argument("--list-folders", action="store_true")
    args = ap.parse_args()

    if args.list_folders:
        list_folders()
        return

    sparse_clone(DEPARTMENT_MAP.keys())
    counts = collect(args.max_per_dept)
    safe_rmtree(CLONE_DIR, ignore_errors=True)

    print("\nDone. Pages copied per department:")
    for dept, n in counts.items():
        print(f"  {dept:12s} {n}")
    print(f"Total: {sum(counts.values())}  ->  {OUT_DIR}/")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"Command failed: {e}")

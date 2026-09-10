"""Create or restore compressed PostgreSQL backups using pg_dump/pg_restore."""
import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("backup", "restore"))
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL 未配置")
    backup_dir = ROOT / "backups"
    backup_dir.mkdir(exist_ok=True)
    if args.action == "backup":
        target = Path(args.path) if args.path else backup_dir / f"classschedule-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.dump"
        subprocess.run(["pg_dump", "--dbname", DATABASE_URL, "--format=custom", "--file", str(target)], check=True)
        print(target.resolve())
        return
    if not args.path:
        raise SystemExit("restore 必须提供备份文件路径")
    source = Path(args.path).resolve()
    if not source.is_file():
        raise SystemExit(f"备份文件不存在：{source}")
    subprocess.run(["pg_restore", "--dbname", DATABASE_URL, "--clean", "--if-exists", "--no-owner", str(source)], check=True)


if __name__ == "__main__":
    main()

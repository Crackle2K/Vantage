#!/usr/bin/env python3
"""
Load the fixed Toronto demo dataset into the local development database.

Used for judges demo dataset (Toronto core).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "demo_businesses.json"

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the fixed Vantage demo dataset.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without modifying MongoDB")
    parser.add_argument("--count", type=int, default=None, help="Only seed the first N matching businesses")
    parser.add_argument("--city", default=None, help="Only seed businesses for one city")
    parser.add_argument("--tag", action="append", default=[], help="Only seed businesses with a matching seed tag")
    parser.add_argument(
        "--i-understand-this-will-modify-db",
        action="store_true",
        help="Allow writes outside ENV=development",
    )
    return parser.parse_args()


def require_safe_mode(args: argparse.Namespace) -> None:
    env_name = str(os.getenv("ENV", "development")).strip().lower()
    if env_name == "development" or args.dry_run or args.i_understand_this_will_modify_db:
        return
    raise SystemExit(
        "Refusing to modify the database outside ENV=development. "
        "Use --i-understand-this-will-modify-db if this is intentional."
    )


def load_seed_rows() -> list[dict[str, Any]]:
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise SystemExit(f"{DATA_FILE} did not contain a JSON array")
    return rows


def filtered_rows(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    tag_filter = {tag.strip().lower() for tag in args.tag if tag.strip()}
    items = rows

    if args.city:
        city = args.city.strip().lower()
        items = [row for row in items if str(row.get("city", "")).strip().lower() == city]

    if tag_filter:
        items = [
            row for row in items
            if tag_filter.intersection({str(tag).strip().lower() for tag in row.get("seed_tags", [])})
        ]

    if args.count is not None:
        items = items[: max(args.count, 0)]

    return items


def build_document(row: dict[str, Any], now: datetime) -> dict[str, Any]:
    doc = dict(row)
    doc.pop("seed_tags", None)
    doc.setdefault("source", "demo_seed_file")
    doc["updated_at"] = now
    return doc


async def seed() -> int:
    args = parse_args()
    require_safe_mode(args)

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "vantage")

    rows = filtered_rows(load_seed_rows(), args)
    if not rows:
        print("matched=0 inserted=0 updated=0")
        return 0

    if args.dry_run:
        print(f"dry_run=1 matched={len(rows)} inserted=0 updated=0 file={DATA_FILE}")
        for row in rows:
            print(f"place_id={row.get('place_id')} city={row.get('city')} name={row.get('name')}")
        return 0

    client = AsyncIOMotorClient(mongo_uri)
    inserted = 0
    updated = 0

    try:
        await client.admin.command("ping")
        businesses = client[database_name]["businesses"]
        now = datetime.utcnow()

        for row in rows:
            doc = build_document(row, now)
            place_id = str(doc.get("place_id") or "").strip()
            if not place_id:
                continue

            existing = await businesses.find_one({"place_id": place_id}, {"_id": 1})
            await businesses.update_one(
                {"place_id": place_id},
                {
                    "$set": doc,
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
            if existing:
                updated += 1
            else:
                inserted += 1

        await businesses.create_index([("location", "2dsphere")])
        await businesses.create_index("place_id", unique=True, sparse=True)

        print(
            f"matched={len(rows)} inserted={inserted} updated={updated} "
            f"database={database_name} file={DATA_FILE.name}"
        )
        return 0
    finally:
        client.close()


def main() -> int:
    try:
        return asyncio.run(seed())
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

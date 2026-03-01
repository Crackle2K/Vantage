#!/usr/bin/env python3
"""
Quick deployment smoke test for Vantage.

Install requirements:
    pip install -r requirements-dev.txt
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 10.0
DEFAULT_LAT = 43.6532
DEFAULT_LNG = -79.3832


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small Vantage API smoke test.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Per-request timeout in seconds")
    parser.add_argument("--expect-version", default=None, help="Expected API version string")
    return parser.parse_args()


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def fail(msg: str) -> None:
    raise AssertionError(msg)


async def fetch_json(
    client: httpx.AsyncClient,
    path: str,
    *,
    expected_status: int = 200,
    params: dict[str, Any] | None = None,
) -> Any:
    response = await client.get(path, params=params)
    if response.status_code != expected_status:
        fail(f"{path} returned {response.status_code}, expected {expected_status}")
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(f"{path} did not return JSON") from exc


def check_health(data: dict[str, Any], expect_version: str | None) -> None:
    if data.get("status") != "ok":
        fail(f"/health returned unexpected status: {data.get('status')!r}")
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        fail("/health did not include a version string")
    if expect_version and version != expect_version:
        fail(f"/health version {version!r} did not match expected {expect_version!r}")


def check_businesses(items: Any) -> None:
    if not isinstance(items, list):
        fail("/api/businesses/nearby did not return a list")
    if not items:
        logging.warning("/api/businesses/nearby returned no businesses")
        return

    first = items[0]
    if not isinstance(first, dict):
        fail("/api/businesses/nearby returned a non-object item")

    required = ["id", "name", "category", "rating", "review_count"]
    missing = [key for key in required if key not in first]
    if missing:
        fail(f"/api/businesses/nearby response is missing fields: {', '.join(missing)}")


async def run() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    logging.info("base_url=%s", base_url)

    async with httpx.AsyncClient(base_url=base_url, timeout=args.timeout, follow_redirects=True) as client:
        health = await fetch_json(client, "/health")
        check_health(health, args.expect_version)
        logging.info("health ok version=%s demo_mode=%s", health.get("version"), health.get("demo_mode"))

        nearby = await fetch_json(
            client,
            "/api/businesses/nearby",
            params={"lat": DEFAULT_LAT, "lng": DEFAULT_LNG, "radius": 8, "limit": 3},
        )
        check_businesses(nearby)
        logging.info("nearby businesses ok count=%s", len(nearby) if isinstance(nearby, list) else 0)

        await fetch_json(client, "/api/auth/me", expected_status=401)
        logging.info("auth guard ok for /api/auth/me")

        await fetch_json(client, "/api/saved", expected_status=401)
        logging.info("auth guard ok for /api/saved")

    logging.info("smoke test passed")
    return 0


def main() -> int:
    configure_logging()
    try:
        return asyncio.run(run())
    except AssertionError as exc:
        logging.error(str(exc))
        return 1
    except httpx.HTTPError as exc:
        logging.error("request failed: %s", exc)
        return 1
    except KeyboardInterrupt:
        logging.warning("cancelled")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

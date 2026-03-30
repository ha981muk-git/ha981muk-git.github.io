#!/usr/bin/env python3
"""
Scrape and download German business documents (PDF) grouped by type.

Usage:
    python scripts/german_doc_scraper.py --seeds seeds --output downloads --target 200 --types all

You supply plain-text seed files (one URL per line) inside the --seeds directory.
Example layout:
    seeds/
        rechnung.txt
        vertrag.txt
        bestellung.txt
        mahnung.txt
        beschwerde.txt
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import pathlib
import sys
import time
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from requests import Response
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

DOC_TYPES: Dict[str, Dict[str, object]] = {
    "rechnung": {
        "english": "invoice",
        "german_label": "Rechnung",
        "keywords": ["rechnung", "invoice", "abr", "rechnung_", "e-rechnung"],
    },
    "vertrag": {
        "english": "contract",
        "german_label": "Vertrag",
        "keywords": ["vertrag", "contract", "vereinbarung"],
    },
    "bestellung": {
        "english": "purchase-order",
        "german_label": "Bestellung",
        "keywords": ["bestellung", "purchase-order", "kaufauftrag", "po"],
    },
    "mahnung": {
        "english": "payment-reminder",
        "german_label": "Mahnung",
        "keywords": ["mahnung", "zahlungserinnerung", "payment-reminder"],
    },
    "beschwerde": {
        "english": "complaint",
        "german_label": "Beschwerde",
        "keywords": ["beschwerde", "reklamation", "complaint"],
    },
}


def read_seed_file(seeds_dir: pathlib.Path, doc_key: str) -> List[str]:
    seed_path = seeds_dir / f"{doc_key}.txt"
    if not seed_path.exists():
        raise FileNotFoundError(f"Missing seed list for '{doc_key}' at {seed_path}")
    with seed_path.open("r", encoding="utf8") as handle:
        return [line.strip() for line in handle if line.strip()]


def is_pdf_response(resp: Response) -> bool:
    ctype = (resp.headers.get("Content-Type") or "").lower()
    return "application/pdf" in ctype or ctype.endswith("/pdf")


def verify_pdf_url(session: requests.Session, url: str, timeout: int = 20) -> bool:
    try:
        resp = session.head(url, allow_redirects=True, timeout=timeout, headers=HEADERS)
        if is_pdf_response(resp):
            return True
    except Exception:
        pass

    try:
        resp = session.get(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers=HEADERS,
            stream=True,
        )
        return is_pdf_response(resp)
    except Exception:
        return False


def extract_pdf_links(
    session: requests.Session,
    page_url: str,
    keywords: Iterable[str],
    polite_delay: float,
) -> List[str]:
    try:
        resp = session.get(page_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[WARN] Cannot load {page_url}: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    matches: Set[str] = set()
    lower_keywords = [kw.lower() for kw in keywords]

    for anchor in soup.find_all("a", href=True):
        raw_href = anchor["href"]
        resolved = urljoin(page_url, raw_href)
        resolved_lower = resolved.lower()
        anchor_text = (anchor.get_text(strip=True) or "").lower()

        if not resolved_lower.startswith(("http://", "https://")):
            continue

        if resolved_lower.endswith(".pdf"):
            matches.add(resolved)
            continue

        if any(kw in resolved_lower for kw in lower_keywords):
            matches.add(resolved)
            continue

        if any(kw in anchor_text for kw in lower_keywords):
            matches.add(resolved)

    confirmed: List[str] = []
    for url in matches:
        if verify_pdf_url(session, url):
            confirmed.append(url)
        time.sleep(polite_delay)
    return confirmed


def sanitize_filename(name: str) -> str:
    keep = "-_.() "
    return "".join(
        c if c.isalnum() or c in keep else "-"
        for c in name
    ).strip("- ") or "document"


def download_pdf(
    session: requests.Session,
    url: str,
    target_dir: pathlib.Path,
    stem: str,
    timeout: int = 60,
) -> Optional[pathlib.Path]:
    try:
        resp = session.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"[WARN] Failed to download {url}: {exc}")
        return None

    if not is_pdf_response(resp):
        print(f"[WARN] Skipping non-PDF URL: {url}")
        return None

    target_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha1(url.encode("utf8")).hexdigest()[:8]
    filename = f"{stem}-{sha}.pdf"
    file_path = target_dir / filename

    with file_path.open("wb") as handle:
        for chunk in resp.iter_content(chunk_size=1024 * 32):
            if chunk:
                handle.write(chunk)
    return file_path


def collect_documents_for_type(
    session: requests.Session,
    doc_key: str,
    seeds: List[str],
    output_root: pathlib.Path,
    target_count: int,
    polite_delay: float,
    metadata_writer,
) -> None:
    meta = DOC_TYPES[doc_key]
    german_label = meta["german_label"]
    keywords = meta["keywords"]
    collected: Set[str] = set()
    dest_dir = output_root / german_label

    for seed_url in seeds:
        if len(collected) >= target_count:
            break

        print(f"[INFO] {german_label}: scanning {seed_url}")
        pdf_links = extract_pdf_links(session, seed_url, keywords, polite_delay)
        if not pdf_links:
            continue

        for link in pdf_links:
            if len(collected) >= target_count:
                break
            if link in collected:
                continue

            stem = f"{german_label}-de-{len(collected)+1:04d}"
            saved_path = download_pdf(session, link, dest_dir, sanitize_filename(stem))
            if saved_path:
                collected.add(link)
                metadata_writer.writerow(
                    {
                        "doc_type_key": doc_key,
                        "doc_type_de": german_label,
                        "doc_type_en": meta["english"],
                        "index": len(collected),
                        "source_url": link,
                        "local_path": str(saved_path),
                    }
                )
                print(f"  ✓ saved #{len(collected)} -> {saved_path}")
                time.sleep(polite_delay)

    print(
        f"[DONE] {german_label}: collected {len(collected)}/{target_count} "
        f"files into {dest_dir}"
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download labeled German business documents (PDF)."
    )
    parser.add_argument(
        "--seeds",
        default="seeds",
        help="Directory holding seed URL lists (default: seeds/)",
    )
    parser.add_argument(
        "--output",
        default="downloads",
        help="Directory where PDFs and metadata.csv are stored",
    )
    parser.add_argument(
        "--types",
        default="all",
        help="Comma-separated list of doc type keys (rechnung,vertrag,...) or 'all'",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=200,
        help="How many PDFs to fetch per document type",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay (seconds) between HTTP requests",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    seeds_dir = pathlib.Path(args.seeds)
    output_root = pathlib.Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)

    enabled_types = (
        DOC_TYPES.keys()
        if args.types == "all"
        else [t.strip().lower() for t in args.types.split(",") if t.strip()]
    )

    unknown = [t for t in enabled_types if t not in DOC_TYPES]
    if unknown:
        raise SystemExit(f"Unknown doc types: {', '.join(unknown)}")

    session = requests.Session()
    metadata_path = output_root / "metadata.csv"

    with metadata_path.open("w", newline="", encoding="utf8") as meta_file:
        writer = csv.DictWriter(
            meta_file,
            fieldnames=[
                "doc_type_key",
                "doc_type_de",
                "doc_type_en",
                "index",
                "source_url",
                "local_path",
            ],
        )
        writer.writeheader()

        for doc_key in enabled_types:
            seeds = read_seed_file(seeds_dir, doc_key)
            collect_documents_for_type(
                session=session,
                doc_key=doc_key,
                seeds=seeds,
                output_root=output_root,
                target_count=args.target,
                polite_delay=args.delay,
                metadata_writer=writer,
            )

    print(f"[OK] Metadata saved to {metadata_path}")


if __name__ == "__main__":
    main()

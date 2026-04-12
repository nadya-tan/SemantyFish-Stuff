import argparse
import json
import re
import time
from pathlib import Path

import requests


def fetch_scientific_name(fish_id, session):
    url = f"https://fishbase.se/summary/{fish_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    resp = session.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    match = re.search(r"<title[^>]*>(.*?)<", resp.text, re.I | re.S)
    if not match:
        return None
    title = match.group(1).strip()
    return title.split(",")[0].strip() if title else None


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Scrape FishBase scientific names for failed species IDs")
    parser.add_argument("--input", default="failed_species_ids.json")
    parser.add_argument("--output", default="failed_species_names.json")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    ids = load_json(input_path)

    existing = {}
    if output_path.exists():
        records = load_json(output_path)
        if isinstance(records, list):
            existing = {int(item["id"]): item for item in records if isinstance(item, dict) and "id" in item}

    session = requests.Session()
    results = []

    for fish_id in ids:
        fish_id = int(fish_id)
        if fish_id in existing:
            results.append(existing[fish_id])
            continue

        try:
            name = fetch_scientific_name(fish_id, session)
            print(f"{fish_id}: {name}")
        except Exception as exc:
            print(f"{fish_id}: failed ({exc})")
            name = None

        results.append({"id": fish_id, "name": name})
        save_json(output_path, results)
        time.sleep(args.delay)

    save_json(output_path, results)
    print(f"Saved {len(results)} records to {output_path}")



if __name__ == "__main__":
    main()

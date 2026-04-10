import requests
import time
import json

BASE = "https://demos.isl.ics.forth.gr/semantyfish-api/resources"
HEADERS = {"accept": "application/json"}

SEARCH_URL = f"{BASE}/search_species"


def extract_species_list(response_json):
    if isinstance(response_json, list):
        return response_json
    if isinstance(response_json, dict):
        return response_json.get("results", [])
    return []


def get_species_by_filter(params):
    res = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    res.raise_for_status()
    data = res.json()
    return extract_species_list(data)


def deduplicate(species_lists):
    species_dict = {}

    for species_list in species_lists:
        for sp in species_list:
            sp_id = sp.get("id")
            if sp_id is not None:
                species_dict[sp_id] = sp

    return list(species_dict.values())


def fetch_data(species_list, delay=0.1):
    """
    Loops through species IDs and fetches full data from /species/{id}.
    """
    all_species_data = []
    failed_ids = []

    for index, sp in enumerate(species_list, start=1):
        sp_id = sp.get("id")
        if sp_id is None:
            continue

        url = f"{BASE}/species/{sp_id}"

        try:
            r = requests.get(url, headers=HEADERS, timeout=20)

            if r.status_code == 200:
                data = r.json()
                all_species_data.append(data)
                print(f"[{index}/{len(species_list)}] Fetched species {sp_id}")
            else:
                print(f"[{index}/{len(species_list)}] Species {sp_id} failed: {r.status_code}")
                failed_ids.append(sp_id)

        except Exception as e:
            print(f"[{index}/{len(species_list)}] Species {sp_id} error: {e}")
            failed_ids.append(sp_id)

        time.sleep(delay)

    return all_species_data, failed_ids


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("Fetching freshwater species")
    freshwater_species = get_species_by_filter({
        "freshwater_environment": "true"
    })
    print(f"Freshwater species: {len(freshwater_species)}")

    print("Fetching brackish water species")
    brackish_species = get_species_by_filter({
        "brackish_water_environment": "true"
    })
    print(f"Brackish water species: {len(brackish_species)}")

    print("Removing duplicates")
    combined_species = deduplicate([freshwater_species, brackish_species])
    print(f"Combined unique total: {len(combined_species)}")

    # save_json("species_list_combined.json", combined_species)
    # print("Output to file")

    print("Fetching full per-species information...")
    all_species_data, failed_ids = fetch_data(combined_species, delay=0.1)

    save_json("all_species_data.json", all_species_data)
    print(f"Saved full species data to all_species_data.json")

    save_json("failed_species_ids.json", failed_ids)
    print(f"Saved failed species IDs to failed_species_ids.json")

    print(f"Total full species records fetched: {len(all_species_data)}")
    print(f"Total failed species records: {len(failed_ids)}")


if __name__ == "__main__":
    main()
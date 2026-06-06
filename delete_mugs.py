"""
delete_mugs.py — Remove all mug listings from Printify (and Etsy).

Reads designs_log.json, finds every published product with blueprint_id 68 (11oz mug),
deletes them from Printify, and marks them as removed in the log.

Run from the Rust & Rainbow folder:
    python3 delete_mugs.py
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")
DESIGNS_LOG = Path("designs_log.json")
MUG_BLUEPRINT_ID = 68

if not PRINTIFY_API_KEY or not PRINTIFY_SHOP_ID:
    print("[ERROR] PRINTIFY_API_KEY or PRINTIFY_SHOP_ID not set in .env")
    exit(1)

if not DESIGNS_LOG.exists():
    print("[ERROR] designs_log.json not found. Nothing to delete.")
    exit(1)

with open(DESIGNS_LOG) as f:
    log = json.load(f)

headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}

to_delete = []
for entry in log:
    for product in entry.get("published_products", []):
        if product.get("blueprint_id") == MUG_BLUEPRINT_ID and product.get("printify_product_id"):
            to_delete.append({
                "design_title": entry["title"],
                "product_name": product["product_name"],
                "printify_product_id": product["printify_product_id"],
                "entry": entry,
                "product": product,
            })

if not to_delete:
    print("No mug products found in designs_log.json.")
    exit(0)

print(f"Found {len(to_delete)} mug listing(s) to delete:\n")
for item in to_delete:
    print(f"  - {item['design_title']} ({item['printify_product_id']})")

confirm = input(f"\nDelete all {len(to_delete)} mug listing(s) from Printify and Etsy? (yes/no): ").strip().lower()
if confirm not in ("yes", "y"):
    print("Cancelled.")
    exit(0)

deleted = 0
for item in to_delete:
    product_id = item["printify_product_id"]
    try:
        resp = requests.delete(
            f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products/{product_id}.json",
            headers=headers
        )
        if resp.status_code in (200, 204):
            print(f"  ✓ Deleted: {item['design_title']} ({product_id})")
            item["product"]["status"] = "deleted"
            deleted += 1
        elif resp.status_code == 404:
            print(f"  ~ Already gone: {item['design_title']} ({product_id})")
            item["product"]["status"] = "deleted"
            deleted += 1
        else:
            print(f"  ✗ Failed: {item['design_title']} — {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  ✗ Error: {item['design_title']} — {e}")

with open(DESIGNS_LOG, "w") as f:
    json.dump(log, f, indent=2)

print(f"\n{deleted}/{len(to_delete)} mug listings deleted. Log updated.")
print("Run 'python3 agent.py --mode generate' to republish with corrected image scaling.")

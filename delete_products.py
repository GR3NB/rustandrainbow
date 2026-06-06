"""
delete_products.py — Remove listings from Printify (and Etsy) by product type.

Usage:
    python3 delete_products.py --type mug
    python3 delete_products.py --type hoodie
    python3 delete_products.py --type tshirt
    python3 delete_products.py --type all
"""

import os
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")
DESIGNS_LOG = Path("designs_log.json")

BLUEPRINT_MAP = {
    "tshirt": 6,
    "mug":    68,
    "hoodie": 77,
}

if not PRINTIFY_API_KEY or not PRINTIFY_SHOP_ID:
    print("[ERROR] PRINTIFY_API_KEY or PRINTIFY_SHOP_ID not set in .env")
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--type", required=True, choices=["tshirt", "mug", "hoodie", "all"],
                    help="Product type to delete")
args = parser.parse_args()

if args.type == "all":
    target_blueprints = set(BLUEPRINT_MAP.values())
else:
    target_blueprints = {BLUEPRINT_MAP[args.type]}

if not DESIGNS_LOG.exists():
    print("[ERROR] designs_log.json not found.")
    exit(1)

with open(DESIGNS_LOG) as f:
    log = json.load(f)

headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}

to_delete = []
for entry in log:
    for product in entry.get("published_products", []):
        if (product.get("blueprint_id") in target_blueprints
                and product.get("printify_product_id")
                and product.get("status") != "deleted"):
            to_delete.append({
                "design_title": entry["title"],
                "product_name": product["product_name"],
                "printify_product_id": product["printify_product_id"],
                "entry": entry,
                "product": product,
            })

if not to_delete:
    print(f"No '{args.type}' products found in designs_log.json.")
    exit(0)

print(f"Found {len(to_delete)} listing(s) to delete:\n")
for item in to_delete:
    print(f"  - {item['design_title']} / {item['product_name']} ({item['printify_product_id']})")

confirm = input(f"\nDelete all {len(to_delete)} listing(s) from Printify and Etsy? (y/yes): ").strip().lower()
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
            print(f"  ✓ Deleted: {item['design_title']} / {item['product_name']}")
            item["product"]["status"] = "deleted"
            deleted += 1
        elif resp.status_code == 404:
            print(f"  ~ Already gone: {item['design_title']} / {item['product_name']}")
            item["product"]["status"] = "deleted"
            deleted += 1
        else:
            print(f"  ✗ Failed: {item['design_title']} — {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  ✗ Error: {item['design_title']} — {e}")

with open(DESIGNS_LOG, "w") as f:
    json.dump(log, f, indent=2)

print(f"\n{deleted}/{len(to_delete)} listing(s) deleted. Log updated.")
print("Run 'python3 agent.py --mode generate' to republish with corrected scaling.")

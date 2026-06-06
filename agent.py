"""
Rust & Rainbow — Automation Agent
Handles design generation, product publishing, social marketing, and performance monitoring.

Usage:
    python agent.py --mode generate     # Generate + approve designs, publish to Etsy
    python agent.py --mode market       # Post to Instagram, TikTok, and Pinterest
    python agent.py --mode monitor      # Weekly sales report + flag underperformers
    python agent.py --mode report       # Weekly AI report + auto-optimize Etsy listings (Monday 7am cron)
    python agent.py --mode all          # Run everything in sequence

Architecture (as of 2026-05-14):

    DESIGN:    Ideogram API → generates images from PROMPTS library
    PRODUCTS:  Printify API → uploads image, creates products, publishes to Etsy
    INSTAGRAM: Meta Graph API (graph.instagram.com/v22.0) → direct post, Facebook cross-posts natively
    TIKTOK:    Zernio API (api.zernio.com) → posts image to TikTok on our behalf
    PINTEREST: Zernio API → posts image to rust-and-rainbow-designs board

    Why Zernio for TikTok/Pinterest:
    TikTok does not allow developers to post to their own account (personal use policy).
    Pinterest direct API requires a multi-week review process for public pins.
    Zernio is an already-approved TikTok and Pinterest developer. We connect our accounts
    to their platform and call their API — they handle platform auth and posting.
    Free tier covers 2 accounts (TikTok + Pinterest) with full API access.

Required .env keys:
    IDEOGRAM_API_KEY, PRINTIFY_API_KEY, PRINTIFY_SHOP_ID
    META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID
    ZERNIO_API_KEY, ZERNIO_TIKTOK_ACCOUNT_ID
    ZERNIO_PINTEREST_ACCOUNT_ID, PINTEREST_BOARD_ID
"""

import os
import sys
import re
import json
import argparse
import requests
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

IDEOGRAM_API_KEY        = os.getenv("IDEOGRAM_API_KEY")
PRINTIFY_API_KEY        = os.getenv("PRINTIFY_API_KEY")
PRINTIFY_SHOP_ID        = os.getenv("PRINTIFY_SHOP_ID")
ETSY_API_KEY            = os.getenv("ETSY_API_KEY")
ETSY_ACCESS_TOKEN       = os.getenv("ETSY_ACCESS_TOKEN")
ETSY_SHOP_ID            = os.getenv("ETSY_SHOP_ID")
META_ACCESS_TOKEN       = os.getenv("META_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID    = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
FB_PAGE_ID              = os.getenv("META_FB_PAGE_ID")
ZERNIO_API_KEY              = os.getenv("ZERNIO_API_KEY")
ZERNIO_TIKTOK_ACCOUNT_ID   = os.getenv("ZERNIO_TIKTOK_ACCOUNT_ID")
ZERNIO_PINTEREST_ACCOUNT_ID = os.getenv("ZERNIO_PINTEREST_ACCOUNT_ID")
PINTEREST_BOARD_ID          = os.getenv("PINTEREST_BOARD_ID")
ANTHROPIC_API_KEY           = os.getenv("ANTHROPIC_API_KEY")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

DESIGNS_LOG     = Path("designs_log.json")
PERFORMANCE_LOG = Path("performance_log.json")
REPORTS_DIR     = Path("reports")

# ─────────────────────────────────────────────
# DESIGN PROMPTS LIBRARY
# ─────────────────────────────────────────────

PROMPTS = [
    # Velcro Dog pillar
    {
        "prompt": "Minimalist single-line art illustration of a vizsla dog, continuous line drawing, white background, clean and modern, suitable for t-shirt print",
        "title": "Velcro Dog Line Art",
        "pillar": "velcro_dog",
        "tags": ["vizsla", "velcro dog", "dog art", "minimalist", "line art", "dog shirt", "vizsla gift"]
    },
    {
        "prompt": "Bold typographic design reading 'VELCRO DOG' with a small vizsla silhouette, clean sans-serif font, minimal, black on white, t-shirt ready",
        "title": "Velcro Dog Typography",
        "pillar": "velcro_dog",
        "tags": ["vizsla", "velcro dog", "funny dog shirt", "vizsla mom", "vizsla dad", "dog humor", "vizsla gift"]
    },
    {
        "prompt": "Retro 1970s vintage poster style featuring a vizsla dog, muted earth tones, rust and tan, bold sans-serif text space, weathered texture",
        "title": "Retro Vizsla Poster",
        "pillar": "hungarian_chaos",
        "tags": ["vizsla", "retro dog", "vintage dog art", "vizsla poster", "dog lover gift", "hungarian pointer"]
    },
    # Gay Dog Dad pillar
    {
        "prompt": "Bold typographic design reading 'TWO DADS. ONE VIZSLA. ZERO REGRETS.' clean sans-serif, minimal layout, small vizsla silhouette, black and rainbow accent",
        "title": "Two Dads Zero Regrets",
        "pillar": "gay_dog_dad",
        "tags": ["gay dog dad", "two dads", "vizsla", "lgbtq dogs", "gay pride", "dog dad shirt", "pride pet"]
    },
    {
        "prompt": "Retro 70s style poster featuring a vizsla dog, bold text reads 'GAY DOG DAD', warm earth tones rust and cream, rainbow stripe accent, vintage feel",
        "title": "Gay Dog Dad Retro",
        "pillar": "gay_dog_dad",
        "tags": ["gay dog dad", "lgbtq", "vizsla", "pride dog", "gay pride shirt", "dog dad", "funny gay shirt"]
    },
    {
        "prompt": "Bold typographic design reading 'THE GAY AGENDA: COFFEE. DOG WALK. BRUNCH. REPEAT.' minimal layout, small vizsla silhouette icon, clean modern type",
        "title": "Gay Agenda",
        "pillar": "gay_dog_dad",
        "tags": ["gay agenda", "gay humor", "lgbtq shirt", "gay dog dad", "funny gay shirt", "pride shirt", "dog lover"]
    },
    # Pride + Breed pillar
    {
        "prompt": "Minimalist vizsla dog silhouette filled with a subtle rainbow gradient, clean modern style, solid flat white background with absolutely no gradient or color bleed into the background, only the dog silhouette contains color, pride flag colors, t-shirt ready, print-ready isolated design",
        "title": "Rainbow Vizsla Silhouette",
        "pillar": "pride_breed",
        "tags": ["vizsla pride", "rainbow dog", "lgbtq dog", "pride pet", "vizsla gift", "gay dog", "pride shirt"]
    },
    {
        "prompt": "Watercolor illustration of a vizsla dog with small rainbow heart detail, loose brushstrokes, warm amber tones, soft and celebratory, white background",
        "title": "Rainbow Heart Vizsla",
        "pillar": "pride_breed",
        "tags": ["vizsla watercolor", "pride dog", "rainbow heart", "lgbtq pet", "dog art", "vizsla gift", "gay pride"]
    },
    # PNW pillar
    {
        "prompt": "Flat vector art vizsla dog silhouette filled with Oregon forest landscape, mountains and pine trees, Pacific Northwest colors, minimal modern style",
        "title": "Oregon Vizsla",
        "pillar": "pnw_dog_life",
        "tags": ["oregon dog", "pnw dog", "vizsla oregon", "pacific northwest", "dog lover", "oregon gift", "vizsla art"]
    },
    # Hungarian Chaos pillar
    {
        "prompt": "Vintage Hungarian hunting dog illustration, vizsla in field pose, woodcut linocut style, two-color print rust and cream, aged texture",
        "title": "Hungarian Hunter",
        "pillar": "hungarian_chaos",
        "tags": ["hungarian vizsla", "hunting dog", "vizsla art", "vintage dog", "dog print", "vizsla gift", "sporting dog"]
    },
    {
        "prompt": "Cute cartoon vizsla puppy with oversized eyes, simple bold outlines, flat color, sticker style, white background, transparent ready",
        "title": "Vizsla Puppy Sticker",
        "pillar": "velcro_dog",
        "tags": ["vizsla sticker", "cute vizsla", "vizsla puppy", "dog sticker", "vizsla decal", "vizsla gift", "dog lover"]
    },
    {
        "prompt": "Cute sticker style vizsla puppy with a small rainbow pride flag tucked firmly under its front paw, flag fully visible and grounded, flat vector art, bright colors, white background, transparent ready",
        "title": "Pride Flag Vizsla",
        "pillar": "gay_dog_dad",
        "tags": ["pride dog", "vizsla pride", "gay dog", "lgbtq pet", "pride sticker", "vizsla sticker", "gay pride"]
    },
]

# Caption templates per pillar
CAPTIONS = {
    "velcro_dog": [
        "Built for the field. Currently velcroed to my leg. 🐕\n\n{hashtags}",
        "My vizsla has zero concept of personal space and I have accepted this. 🐾\n\n{hashtags}",
        "Warning: may stop suddenly to cuddle. 🐕\n\n{hashtags}",
        "I didn't choose the velcro life. The velcro life chose me. 🐾\n\n{hashtags}",
    ],
    "gay_dog_dad": [
        "Two dads. One vizsla. Zero regrets. 🌈🐕\n\n{hashtags}",
        "The gay agenda: coffee. dog walk. brunch. repeat. 🌈\n\n{hashtags}",
        "Gay dog dad reporting for duty. 🐾🌈\n\n{hashtags}",
        "My dog has two dads and he is absolutely thriving. 🌈🐕\n\n{hashtags}",
    ],
    "pride_breed": [
        "Proud owner. Proud vizsla. 🌈🐕\n\n{hashtags}",
        "Rust and rainbow. That's the whole vibe. 🌈\n\n{hashtags}",
        "Part hunting dog. Part pride icon. 🌈🐾\n\n{hashtags}",
    ],
    "pnw_dog_life": [
        "Oregon raised. Vizsla obsessed. 🌲🐕\n\n{hashtags}",
        "Pacific Northwest dog dad energy. 🌲🐾\n\n{hashtags}",
    ],
    "hungarian_chaos": [
        "Hungarian bred. Chaos guaranteed. 🐕\n\n{hashtags}",
        "Part hunting dog. Part barnacle. Full chaos. 🐾\n\n{hashtags}",
        "Built different. Clingier too. 🐕\n\n{hashtags}",
    ],
}

HASHTAG_SETS = {
    # ── Broad reach — high volume discovery (100M+ posts) ──────────────────────
    "broad_dog": "#dogsofinstagram #dogstagram #dogsofig #doglife #dogmom #dogdad #doglovers #dogs",

    # ── Vizsla niche — core breed community ────────────────────────────────────
    "vizsla": (
        "#vizsla #vizslaofinstagram #vizslanation #vizslalife #velcrodog "
        "#hungarianpointer #hungarianvizsla #vizslapuppy #vizslagram #vizsladog"
    ),

    # ── Pride / LGBTQ+ — used on gay_dog_dad and pride_breed pillars ───────────
    "gay_dog_dad": (
        "#gaydogdad #lgbtqdogs #gaydogs #twodads #gaypride #lgbtpets #pridedog "
        "#lgbtq #gaypets #pridemonth #queerdogdad #gaydog"
    ),

    # ── Print-on-demand / shop discovery ───────────────────────────────────────
    "pod": (
        "#dogtshirt #dogshirt #dogsticker #customdogshirt #dogmerchandise "
        "#etsyshop #etsyseller #etsyfinds #shopsmall #smallbusiness #handmade"
    ),

    # ── PNW / Oregon local ──────────────────────────────────────────────────────
    "pnw": "#oregondogs #pnwdogs #portlanddog #pnwlife #oregonlife #pacificnorthwest",

    # ── TikTok-specific discovery (FYP + dogtok ecosystem) ─────────────────────
    # Used only in the TikTok description field — not sent to Instagram/Pinterest.
    "tiktok_discovery": "#dogtok #dogsoftiktok #tiktokdogs #fyp #foryoupage #foryou #petlover #pettok",
}

# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────

def load_designs_log():
    if DESIGNS_LOG.exists():
        with open(DESIGNS_LOG) as f:
            return json.load(f)
    return []

def save_designs_log(log):
    with open(DESIGNS_LOG, "w") as f:
        json.dump(log, f, indent=2)

def header(text):
    print(f"\n{'─'*50}")
    print(f"  {text}")
    print(f"{'─'*50}\n")

REQUIRED_ENV = {
    "generate": ["IDEOGRAM_API_KEY", "PRINTIFY_API_KEY", "PRINTIFY_SHOP_ID"],
    "market":   ["META_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID",
                 "ZERNIO_API_KEY", "ZERNIO_TIKTOK_ACCOUNT_ID"],
    "monitor":  ["PRINTIFY_API_KEY", "PRINTIFY_SHOP_ID"],
    # report: Claude API optional — collects data regardless; narrative generated if key present
    "report":   ["PRINTIFY_API_KEY", "PRINTIFY_SHOP_ID"],
}

def check_env(mode):
    keys = REQUIRED_ENV.get(mode, [])
    missing = [k for k in keys if not os.getenv(k) or os.getenv(k).startswith("your_") or os.getenv(k).startswith("pending_")]
    if missing:
        print(f"\n[ERROR] Missing or unset env vars for --mode {mode}:")
        for k in missing:
            print(f"  - {k}")
        print("Add them to .env and retry.\n")
        sys.exit(1)

# ─────────────────────────────────────────────
# PHASE 1: DESIGN GENERATION
# ─────────────────────────────────────────────

def generate_designs(num=5):
    """Call Ideogram API to generate designs from the prompt library."""
    header("GENERATING DESIGNS")

    # Skip prompts whose title already has a published entry in the log.
    # Prevents re-generating (and re-listing on Etsy) designs that already exist.
    log = load_designs_log()
    published_titles = {d["title"] for d in log if d.get("status") == "published"}
    available_prompts = [p for p in PROMPTS if p["title"] not in published_titles]
    if len(available_prompts) < num:
        print(f"  Note: only {len(available_prompts)} unpublished designs available (requested {num}).")
    if not available_prompts:
        print("  All prompts in the library are already published. Add new prompts to PROMPTS to generate more.")
        return []

    selected_prompts = random.sample(available_prompts, min(num, len(available_prompts)))
    generated = []

    for i, p in enumerate(selected_prompts):
        print(f"[{i+1}/{len(selected_prompts)}] Generating: {p['title']}")
        try:
            response = requests.post(
                "https://api.ideogram.ai/generate",
                headers={
                    "Api-Key": IDEOGRAM_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "image_request": {
                        "prompt": p["prompt"],
                        "aspect_ratio": "ASPECT_1_1",
                        "model": "V_2",
                        "magic_prompt_option": "AUTO"
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            image_url = data["data"][0]["url"]

            # Download image
            img_path = OUTPUT_DIR / f"{p['title'].replace(' ', '_').lower()}_{int(time.time())}.png"
            img_data = requests.get(image_url).content
            with open(img_path, "wb") as f:
                f.write(img_data)

            generated.append({
                "title": p["title"],
                "pillar": p["pillar"],
                "tags": p["tags"],
                "image_path": str(img_path),
                "image_url": image_url,
                "prompt": p["prompt"],
                "generated_at": datetime.now().isoformat(),
                "status": "pending_approval"
            })
            print(f"   ✓ Saved to {img_path}")
            time.sleep(1)  # Rate limit courtesy

        except Exception as e:
            print(f"   ✗ Failed: {e}")

    return generated

def review_designs(designs):
    """Present each design for Ryan's approval."""
    header("DESIGN REVIEW — Approve or Skip Each")
    print("Opening designs for review. Type A to approve, S to skip, Q to quit.\n")
    approved = []

    for i, d in enumerate(designs):
        print(f"[{i+1}/{len(designs)}] {d['title']} ({d['pillar']})")
        print(f"  File: {d['image_path']}")
        # Open image for viewing
        os.system(f"open '{d['image_path']}'")
        while True:
            choice = input("  Approve (A) / Skip (S) / Quit (Q): ").strip().upper()
            if choice == "A":
                d["status"] = "approved"
                approved.append(d)
                print("  ✓ Approved")
                break
            elif choice == "S":
                d["status"] = "skipped"
                print("  → Skipped")
                break
            elif choice == "Q":
                print("\nReview paused. Run again to continue.")
                return approved
            else:
                print("  Please enter A, S, or Q.")

    print(f"\n{len(approved)} designs approved out of {len(designs)} reviewed.")
    return approved

# ─────────────────────────────────────────────
# PHASE 1: PRINTIFY + ETSY PUBLISHING
# ─────────────────────────────────────────────

# Printify blueprint IDs for common products
PRINTIFY_BLUEPRINTS = {
    "unisex_tshirt": 6,      # Unisex Softstyle T-Shirt
    "mug_11oz": 68,          # White Glossy Mug 11oz
    "hoodie": 77,            # Unisex Hoodie
    "sticker": 400,          # Kiss-Cut Stickers (2"–4" square, verified from catalog)
}

PRINTIFY_PRINT_AREA = {
    6:   {"id": "front", "width": 4500, "height": 5400},
    68:  {"id": "front", "width": 2400, "height": 2400},
    77:  {"id": "front", "width": 4500, "height": 5400},
    400: {"id": "front", "width": 1200, "height": 1200},
}

def get_provider_and_variants(blueprint_id):
    """Fetch the first available print provider and its enabled variants for a blueprint.

    Printify requires real variant IDs at product creation time — you can't send empty arrays.
    This fetches them live from the catalog so we always use valid IDs.
    """
    headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}

    # Get available providers for this blueprint
    providers_resp = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers.json",
        headers=headers
    )
    providers_resp.raise_for_status()
    providers = providers_resp.json()

    if not providers:
        raise ValueError(f"No print providers found for blueprint {blueprint_id}")

    provider_id = providers[0]["id"]
    provider_title = providers[0].get("title", str(provider_id))

    # Get variants for this provider/blueprint combo
    variants_resp = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json",
        headers=headers
    )
    variants_resp.raise_for_status()
    all_variants = variants_resp.json().get("variants", [])

    # Filter to variants that are actually available
    enabled = [v for v in all_variants if v.get("is_available", True)]
    if not enabled:
        enabled = all_variants  # Fallback: use all if none marked available

    return provider_id, provider_title, enabled


# Default retail prices per blueprint (in cents)
PRODUCT_PRICES = {
    6:   2500,  # T-shirt: $25.00
    68:  1800,  # Mug 11oz: $18.00
    77:  5500,  # Hoodie: $55.00
    400:  800,  # Kiss-Cut Sticker: $8.00
}

# Image scale per blueprint.
# Mugs have a wide rectangular print area (wider than tall). A square 1:1 image at scale=1
# overflows the height and clips the top/bottom. Lower scale keeps the whole design visible.
# Hoodies have a tall front print area like t-shirts but the chest width is narrower relative
# to the full print area — scale down slightly to keep designs from reaching the seams.
PRODUCT_IMAGE_SCALE = {
    6:   1.0,   # T-shirt: tall print area, square image fits fine
    68:  0.41,  # Mug: print area is 2700x1120 (2.4:1 ratio). Scale = 1120/2700 to fit full square image
    77:  0.67,  # Hoodie: print area is 3213x2141 (1.5:1 ratio). Scale = 2141/3213 to fit full square image
    400: 1.0,   # Kiss-Cut Sticker: 1:1 print area, square image fills it cleanly
}


def upload_image_to_printify_cdn(image_path):
    """Upload a local image file to Printify and return its permanent CDN preview URL.

    Printify hosts all uploaded images on CloudFront (permanent, no expiry).
    This is used both during product creation and as a fallback when social posting
    encounters an expired Ideogram URL.
    """
    import base64
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    resp = requests.post(
        "https://api.printify.com/v1/uploads/images.json",
        headers={"Authorization": f"Bearer {PRINTIFY_API_KEY}"},
        json={
            "file_name": Path(image_path).name,
            "contents": base64.b64encode(img_bytes).decode()
        }
    )
    resp.raise_for_status()
    data = resp.json()
    preview_url = data.get("preview_url")
    image_id = data.get("id")
    if not preview_url:
        raise ValueError(f"Printify upload succeeded but returned no preview_url. Keys: {list(data.keys())}")
    return image_id, preview_url


def get_postable_image_url(design, log=None, log_path=None):
    """Return a publicly accessible image URL suitable for social posting.

    Priority:
      1. mockup_url — permanent Printify CDN URL saved at generate time (best)
      2. image_url  — Ideogram URL, valid for ~24h after generation (may be expired)
      3. local file — re-upload the saved local file to Printify CDN (fallback)

    If the fallback is used, saves the new CDN URL back to designs_log so
    future posts don't need to re-upload.
    """
    # Best case: permanent Printify CDN URL already saved
    if design.get("mockup_url"):
        return design["mockup_url"]

    # Try the Ideogram URL (valid for ~24h)
    image_url = design.get("image_url")
    if image_url:
        try:
            r = requests.head(image_url, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                return image_url
            print(f"  Image URL returned {r.status_code} — URL has expired.")
        except Exception:
            print("  Image URL unreachable.")

    # Fallback: re-upload local file to Printify CDN
    image_path = design.get("image_path")
    if image_path and Path(image_path).exists():
        print(f"  Re-uploading local file to Printify CDN: {image_path}")
        try:
            _, cdn_url = upload_image_to_printify_cdn(image_path)
            design["mockup_url"] = cdn_url
            print(f"  ✓ CDN URL saved for future use.")
            # Persist the new URL back to designs_log if caller passes it
            if log is not None and log_path is not None:
                save_designs_log(log)
            return cdn_url
        except Exception as e:
            print(f"  ✗ Re-upload failed: {e}")
    else:
        print(f"  Local image file not found at: {image_path}")

    return None


def upload_to_printify(design):
    """Upload image to Printify and create products, then publish to connected Etsy store.

    Requires Etsy to be connected in Printify's dashboard:
    printify.com > Manage My Stores > Connect a sales channel > Etsy
    No Etsy API key needed — Printify handles the Etsy connection.

    Returns (published_products, cdn_preview_url). The cdn_preview_url is the
    permanent Printify CloudFront URL for the uploaded image — save it as
    design["mockup_url"] for reliable social posting.
    """
    header(f"PUBLISHING: {design['title']}")
    printify_headers = {
        "Authorization": f"Bearer {PRINTIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    published_products = []
    cdn_preview_url = None  # Will be set from first successful upload

    for product_name, blueprint_id in PRINTIFY_BLUEPRINTS.items():
        print(f"  Creating {product_name}...")
        try:
            # Step 1: Upload image to Printify (also captures permanent CDN URL)
            with open(design["image_path"], "rb") as img_file:
                img_bytes = img_file.read()

            upload_resp = requests.post(
                "https://api.printify.com/v1/uploads/images.json",
                headers={"Authorization": f"Bearer {PRINTIFY_API_KEY}"},
                json={
                    "file_name": f"{design['title'].replace(' ', '_')}.png",
                    "contents": __import__('base64').b64encode(img_bytes).decode()
                }
            )
            upload_resp.raise_for_status()
            upload_data = upload_resp.json()
            image_id = upload_data["id"]
            # Capture the permanent CDN URL from the first successful upload
            if cdn_preview_url is None:
                cdn_preview_url = upload_data.get("preview_url")

            # Step 2: Fetch real provider + variant IDs from Printify catalog
            provider_id, provider_title, catalog_variants = get_provider_and_variants(blueprint_id)
            print(f"    Provider: {provider_title} ({len(catalog_variants)} variants)")

            # Limit variants to first 30 to avoid timeouts (covers all common sizes/colors)
            selected_variants = catalog_variants[:30]
            variant_ids = [v["id"] for v in selected_variants]
            price = PRODUCT_PRICES.get(blueprint_id, 2000)

            product_variants = [
                {"id": v["id"], "price": price, "is_enabled": True}
                for v in selected_variants
            ]

            # Step 3: Build print area
            area = PRINTIFY_PRINT_AREA[blueprint_id]
            image_scale = PRODUCT_IMAGE_SCALE.get(blueprint_id, 1.0)

            # Step 4: Create product
            product_payload = {
                "title": f"{design['title']} | Rust & Rainbow",
                "description": build_etsy_description(design),
                "blueprint_id": blueprint_id,
                "print_provider_id": provider_id,
                "variants": product_variants,
                "print_areas": [
                    {
                        "variant_ids": variant_ids,
                        "placeholders": [
                            {
                                "position": area["id"],
                                "images": [
                                    {
                                        "id": image_id,
                                        "x": 0.5,
                                        "y": 0.5,
                                        "scale": image_scale,
                                        "angle": 0
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }

            create_resp = requests.post(
                f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products.json",
                headers=printify_headers,
                json=product_payload
            )
            create_resp.raise_for_status()
            product_id = create_resp.json()["id"]

            # Step 5: Publish to connected Etsy store via Printify
            publish_resp = requests.post(
                f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products/{product_id}/publish.json",
                headers=printify_headers,
                json={
                    "title": True,
                    "description": True,
                    "images": True,
                    "variants": True,
                    "tags": True,
                    "keyFeatures": True,
                    "shipping_template": True
                }
            )
            publish_resp.raise_for_status()

            published_products.append({
                "product_name": product_name,
                "printify_product_id": product_id,
                "blueprint_id": blueprint_id,
                "provider_id": provider_id
            })
            print(f"  ✓ {product_name} published to Etsy via Printify")
            time.sleep(2)

        except Exception as e:
            print(f"  ✗ {product_name} failed: {e}")

    return published_products, cdn_preview_url

def build_etsy_description(design):
    pillar_descriptions = {
        "velcro_dog": "For vizsla owners who know the velcro dog life isn't a choice — it's a calling.",
        "gay_dog_dad": "For proud gay dog dads living their best two-dads-one-dog life.",
        "pride_breed": "Breed pride meets rainbow pride. Made for vizsla owners who are unapologetically themselves.",
        "pnw_dog_life": "Pacific Northwest vizsla energy. For Oregon dog people.",
        "hungarian_chaos": "Hungarian bred, chaos guaranteed. For the vizsla parents who know exactly what this means.",
    }
    description = pillar_descriptions.get(design["pillar"], "Designed for vizsla lovers.")
    return f"""{description}

Designed by Rust & Rainbow — a small brand for gay dog owners and vizsla enthusiasts.

• High-quality print-on-demand product
• Ships within 3-7 business days
• Printed and fulfilled by Printify

Tags: {', '.join(design['tags'])}
"""

# ─────────────────────────────────────────────
# PHASE 2: INSTAGRAM AUTO-POSTING
# ─────────────────────────────────────────────

def build_caption(design):
    """Generate an Instagram/Pinterest caption with a full hashtag stack.

    Strategy: broad reach tags first (high volume discovery), then niche breed
    tags (engaged community), then pillar-specific tags, then shop/POD tags.
    This gives the algorithm a wide funnel that narrows into the core audience.
    """
    templates = CAPTIONS.get(design["pillar"], CAPTIONS["velcro_dog"])
    template = random.choice(templates)
    pillar = design["pillar"]

    tag_parts = [
        HASHTAG_SETS["broad_dog"],
        HASHTAG_SETS["vizsla"],
    ]
    if "gay" in pillar or "pride" in pillar:
        tag_parts.append(HASHTAG_SETS["gay_dog_dad"])
    if "pnw" in pillar:
        tag_parts.append(HASHTAG_SETS["pnw"])
    tag_parts.append(HASHTAG_SETS["pod"])
    tag_parts.append("#rustandrainbow")

    # Instagram hard limit is 30 hashtags — trim from the end (least specific tags last)
    all_tags = " ".join(tag_parts).split()
    if len(all_tags) > 30:
        all_tags = all_tags[:30]

    return template.format(hashtags=" ".join(all_tags))


def build_tiktok_description(design):
    """Build the TikTok description field (up to 4000 chars) — separate from the caption title.

    TikTok photo posts have a 90-char title limit but an unlimited description
    field in tiktokSettings. We put all hashtags here so the title stays clean
    as a hook and the algorithm still gets full hashtag signal for discovery.
    """
    pillar = design["pillar"]

    tag_parts = [
        HASHTAG_SETS["tiktok_discovery"],
        HASHTAG_SETS["vizsla"],
    ]
    if "gay" in pillar or "pride" in pillar:
        tag_parts.append(HASHTAG_SETS["gay_dog_dad"])
    if "pnw" in pillar:
        tag_parts.append(HASHTAG_SETS["pnw"])
    tag_parts.append(HASHTAG_SETS["pod"])
    tag_parts.append("#rustandrainbow")

    return " ".join(tag_parts)

IG_BASE = "https://graph.instagram.com/v22.0"

def post_to_instagram(design, image_url):
    """Post a product image to Instagram via Instagram Graph API.

    image_url must be a publicly accessible JPEG or PNG (Instagram fetches it server-side).
    Best sources in priority order:
      1. Printify mockup URL (after publishing)
      2. Ideogram generation URL (already public, may expire after ~24h)
    """
    caption = build_caption(design)
    print(f"  Posting to Instagram: {design['title']}")
    try:
        # Step 1: Create media container
        container_resp = requests.post(
            f"{IG_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": META_ACCESS_TOKEN
            }
        )
        container_resp.raise_for_status()
        container_id = container_resp.json()["id"]
        print(f"  Container created: {container_id}")

        # Step 2: Poll until container is ready (Instagram needs time to fetch the image)
        for attempt in range(10):
            time.sleep(3)
            status_resp = requests.get(
                f"{IG_BASE}/{container_id}",
                params={"fields": "status_code", "access_token": META_ACCESS_TOKEN}
            )
            status_code = status_resp.json().get("status_code", "UNKNOWN")
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                raise Exception("Instagram container processing failed")
            print(f"  Waiting for container... ({status_code})")
        else:
            raise Exception("Instagram container timed out after 30s")

        # Step 3: Publish container
        publish_resp = requests.post(
            f"{IG_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": META_ACCESS_TOKEN
            }
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json()["id"]
        print(f"  ✓ Posted to Instagram (post ID: {post_id})")
        return post_id

    except requests.HTTPError as e:
        print(f"  ✗ Instagram post failed: {e.response.status_code} {e.response.text}")
        return None
    except Exception as e:
        print(f"  ✗ Instagram post failed: {e}")
        return None

# ─────────────────────────────────────────────
# PHASE 3: TIKTOK + PINTEREST VIA ZERNIO
# ─────────────────────────────────────────────

ZERNIO_BASE = "https://api.zernio.com"

def _zernio_headers():
    return {
        "Authorization": f"Bearer {ZERNIO_API_KEY}",
        "Content-Type": "application/json"
    }

def post_to_tiktok(image_url, caption, description=""):
    """Post a design image to TikTok via Zernio.

    caption     — the hook line shown as the photo title (90-char hard limit).
                  Keep it clean: just the hook text, no hashtags.
    description — goes into tiktokSettings.description (up to 4000 chars).
                  This is where all hashtags live — separate from the title limit.

    Zernio is an approved TikTok developer and handles posting on our behalf.
    TikTok image posts are supported and perform well for product designs.
    """
    print(f"  Posting to TikTok via Zernio: {caption[:50]}...")

    if not ZERNIO_API_KEY or not ZERNIO_TIKTOK_ACCOUNT_ID:
        print("  ✗ ZERNIO_API_KEY or ZERNIO_TIKTOK_ACCOUNT_ID not set. Skipping.")
        return None
    if ZERNIO_TIKTOK_ACCOUNT_ID.startswith("pending"):
        print("  ✗ TikTok not yet connected in Zernio dashboard. Skipping.")
        return None

    try:
        resp = requests.post(
            f"{ZERNIO_BASE}/v1/posts",
            headers=_zernio_headers(),
            json={
                "content": caption,
                "platforms": [
                    {"platform": "tiktok", "accountId": ZERNIO_TIKTOK_ACCOUNT_ID}
                ],
                "mediaItems": [{"url": image_url, "type": "image"}],
                "publishNow": True,
                "tiktokSettings": {
                    "privacyLevel": "PUBLIC_TO_EVERYONE",
                    "allowComment": True,
                    "autoAddMusic": True,
                    "contentPreviewConfirmed": True,
                    "expressConsentGiven": True,
                    **({"description": description[:4000]} if description else {}),
                }
            }
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            print(f"  ✗ TikTok post failed: {data['error']}")
            return None
        post_id = data.get("post", {}).get("_id")
        print(f"  ✓ Posted to TikTok via Zernio (post ID: {post_id})")
        return post_id

    except requests.HTTPError as e:
        print(f"  ✗ TikTok post failed: {e.response.status_code} {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"  ✗ TikTok post failed: {e}")
        return None


def post_to_pinterest(image_url, caption, design):
    """Post a design image to Pinterest via Zernio.

    Pins to the Rust & Rainbow Designs board. Pinterest is evergreen —
    pins drive Etsy traffic for months after posting.

    Requires ZERNIO_PINTEREST_ACCOUNT_ID and PINTEREST_BOARD_ID in .env.
    Connect Pinterest at zernio.com dashboard, then update both values.
    """
    print(f"  Posting to Pinterest via Zernio: {design['title']}...")

    if not ZERNIO_PINTEREST_ACCOUNT_ID or ZERNIO_PINTEREST_ACCOUNT_ID.startswith("pending"):
        print("  ✗ Pinterest not yet connected in Zernio. Skipping.")
        print("    → Connect Pinterest at zernio.com, then update ZERNIO_PINTEREST_ACCOUNT_ID and PINTEREST_BOARD_ID in .env")
        return None
    if not PINTEREST_BOARD_ID or PINTEREST_BOARD_ID.startswith("pending"):
        print("  ✗ PINTEREST_BOARD_ID not set in .env. Skipping.")
        return None

    try:
        # Pinterest needs a title — use design title, 100 char max
        pin_title = f"{design['title']} | Rust & Rainbow"[:100]

        # Strip hashtags from caption for Pinterest description (they don't help there)
        description = caption.split("\n\n")[0]  # Just the caption text, no hashtag block

        resp = requests.post(
            f"{ZERNIO_BASE}/v1/posts",
            headers=_zernio_headers(),
            json={
                "content": description,
                "platforms": [
                    {"platform": "pinterest", "accountId": ZERNIO_PINTEREST_ACCOUNT_ID}
                ],
                "mediaItems": [{"url": image_url, "type": "image"}],
                "publishNow": True,
                "platformSpecificData": {
                    "pinterest": {
                        "boardId": PINTEREST_BOARD_ID,
                        "title": pin_title
                    }
                }
            }
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            print(f"  ✗ Pinterest post failed: {data['error']}")
            return None
        post_id = data.get("post", {}).get("_id")
        print(f"  ✓ Posted to Pinterest via Zernio (post ID: {post_id})")
        return post_id

    except requests.HTTPError as e:
        print(f"  ✗ Pinterest post failed: {e.response.status_code} {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"  ✗ Pinterest post failed: {e}")
        return None

# ─────────────────────────────────────────────
# PHASE 4: PERFORMANCE MONITOR
# ─────────────────────────────────────────────

def run_monitor():
    """Pull Etsy sales data and flag underperformers."""
    header("PERFORMANCE MONITOR")
    log = load_designs_log()

    if not log:
        print("No designs in log yet. Run --mode generate first.")
        return

    print(f"Checking {len(log)} designs...\n")
    flagged = []
    thirty_days_ago = datetime.now() - timedelta(days=30)

    for entry in log:
        published_at = datetime.fromisoformat(entry.get("published_at", datetime.now().isoformat()))
        sales = entry.get("sales", 0)
        title = entry.get("title", "Unknown")

        if published_at < thirty_days_ago and sales == 0:
            flagged.append(entry)
            print(f"  ⚠ ZERO SALES (30+ days): {title}")
        elif sales > 0:
            print(f"  ✓ {title}: {sales} sale(s)")
        else:
            days_live = (datetime.now() - published_at).days
            print(f"  ○ {title}: {days_live} days live, no sales yet (under 30 day threshold)")

    if flagged:
        print(f"\n{len(flagged)} design(s) flagged for removal.")
        print("Review the flagged designs above and decide:")
        for f in flagged:
            while True:
                choice = input(f"  Remove '{f['title']}'? (Y/N): ").strip().upper()
                if choice == "Y":
                    remove_listing(f)
                    f["status"] = "removed"
                    break
                elif choice == "N":
                    print(f"  Keeping '{f['title']}' — will check again next week.")
                    break
        save_designs_log(log)
    else:
        print("\nAll designs within acceptable performance range.")

def remove_listing(design):
    """Remove a product from Printify and Etsy."""
    for product in design.get("published_products", []):
        try:
            resp = requests.delete(
                f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/products/{product['printify_product_id']}.json",
                headers={"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
            )
            resp.raise_for_status()
            print(f"  ✓ Removed {design['title']} ({product['product_name']}) from Printify/Etsy")
        except Exception as e:
            print(f"  ✗ Failed to remove {design['title']}: {e}")

# ─────────────────────────────────────────────
# PHASE 5: WEEKLY REPORT + SELF-LEARNING LOOP
# ─────────────────────────────────────────────

def load_performance_log():
    """Load the weekly performance log. Returns dict with 'weeks' list."""
    if PERFORMANCE_LOG.exists():
        with open(PERFORMANCE_LOG) as f:
            return json.load(f)
    return {"weeks": []}

def save_performance_log(log):
    with open(PERFORMANCE_LOG, "w") as f:
        json.dump(log, f, indent=2)

def get_printify_orders():
    """Fetch real order counts from Printify.

    Returns (total_orders, revenue_this_week_cents, orders_this_week_count).
    Fixes the hardcoded sales=0 bug in the old monitor mode.
    """
    headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
    try:
        resp = requests.get(
            f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/orders.json",
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        all_orders = data.get("data", [])
        total = data.get("total", len(all_orders))

        week_ago = datetime.now() - timedelta(days=7)
        this_week = []
        for order in all_orders:
            created_raw = order.get("created_at", "")
            if created_raw:
                try:
                    order_dt = datetime.fromisoformat(created_raw[:19])
                    if order_dt > week_ago:
                        this_week.append(order)
                except (ValueError, TypeError):
                    pass

        # total_price is in cents for USD shops
        revenue_cents = sum(o.get("total_price", 0) for o in this_week)
        return total, revenue_cents, len(this_week)

    except Exception as e:
        print(f"  ✗ Printify orders fetch failed: {e}")
        return 0, 0, 0

def get_etsy_listing_stats(prev_week_data):
    """Fetch per-listing view and favorite counts from Etsy, calculate weekly deltas.

    Requires ETSY_ACCESS_TOKEN (run etsy_auth.py first).
    If token is absent, returns None and skips gracefully.
    Etsy visit/search traffic is NOT exposed via API — we track cumulative views
    and calculate week-over-week deltas as a proxy for traffic.
    """
    _missing = (
        not ETSY_ACCESS_TOKEN
        or not ETSY_API_KEY
        or not ETSY_SHOP_ID
        or ETSY_ACCESS_TOKEN.startswith("your_")
        or ETSY_ACCESS_TOKEN.startswith("pending_")
    )
    if _missing:
        print("  ⚠ Etsy API not configured — run etsy_auth.py to enable listing analytics.")
        print("    (Etsy keys: ETSY_API_KEY, ETSY_ACCESS_TOKEN, ETSY_SHOP_ID in .env)")
        return None

    headers = {
        "Authorization": f"Bearer {ETSY_ACCESS_TOKEN}",
        "x-api-key": ETSY_API_KEY
    }
    try:
        resp = requests.get(
            f"https://openapi.etsy.com/v3/application/shops/{ETSY_SHOP_ID}/listings/active",
            headers=headers,
            params={"limit": 100, "includes": "stats"}
        )
        resp.raise_for_status()
        data = resp.json()
        listings = data.get("results", [])

        # Build previous-week lookup for delta calculation
        prev_map = {}
        if prev_week_data:
            for l in prev_week_data.get("listings", []):
                prev_map[str(l.get("listing_id"))] = l

        stats = []
        for listing in listings:
            listing_id = str(listing.get("listing_id", ""))
            views = listing.get("views", 0)
            favorites = listing.get("num_favorers", 0)
            prev = prev_map.get(listing_id, {})
            # First week: delta = 0 (no baseline). Subsequent weeks: actual change.
            views_delta    = views    - prev.get("views", views)
            favorites_delta = favorites - prev.get("favorites", favorites)
            stats.append({
                "listing_id": listing_id,
                "title": listing.get("title", ""),
                "views": views,
                "views_delta": max(views_delta, 0),  # Never negative (catches API quirks)
                "favorites": favorites,
                "favorites_delta": max(favorites_delta, 0),
                "state": listing.get("state", ""),
                "url": listing.get("url", "")
            })

        return stats

    except Exception as e:
        print(f"  ✗ Etsy listing stats fetch failed: {e}")
        return None

def get_instagram_insights():
    """Fetch Instagram account metrics and recent post engagement.

    Returns dict with: follower_count, media_count, reach, impressions,
    profile_views, recent_posts (list of posts from the last 7 days).
    """
    if not META_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        print("  ⚠ Instagram credentials not configured — skipping.")
        return None

    result = {}

    # Account-level metrics (follower count, total media)
    try:
        acct_resp = requests.get(
            f"{IG_BASE}/{INSTAGRAM_ACCOUNT_ID}",
            params={
                "fields": "followers_count,media_count",
                "access_token": META_ACCESS_TOKEN
            }
        )
        acct_resp.raise_for_status()
        acct_data = acct_resp.json()
        result["follower_count"] = acct_data.get("followers_count", 0)
        result["media_count"]    = acct_data.get("media_count", 0)
    except Exception as e:
        print(f"  ✗ Instagram account fetch failed: {e}")

    # Weekly insights (reach, impressions) — requires instagram_manage_insights permission
    # If the token doesn't have it, this silently skips (not an error worth surfacing)
    try:
        ins_resp = requests.get(
            f"{IG_BASE}/{INSTAGRAM_ACCOUNT_ID}/insights",
            params={
                "metric": "reach,impressions",
                "period": "week",
                "access_token": META_ACCESS_TOKEN
            }
        )
        if ins_resp.status_code == 200:
            for item in ins_resp.json().get("data", []):
                name = item["name"]
                values = item.get("values", [])
                if values:
                    result[name] = values[-1].get("value", 0)
        # 400 = missing instagram_manage_insights permission — not an error, just skip
    except Exception:
        pass

    # Recent posts (last 7 days)
    try:
        week_ago = datetime.now() - timedelta(days=7)
        media_resp = requests.get(
            f"{IG_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
            params={
                "fields": "id,caption,timestamp,like_count,comments_count,permalink",
                "access_token": META_ACCESS_TOKEN
            }
        )
        media_resp.raise_for_status()
        media_data = media_resp.json()

        recent_posts = []
        for post in media_data.get("data", [])[:20]:
            ts = post.get("timestamp", "")
            if ts:
                try:
                    post_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                    if post_dt > week_ago:
                        recent_posts.append({
                            "id": post["id"],
                            "caption_preview": (post.get("caption") or "")[:80],
                            "likes": post.get("like_count", 0),
                            "comments": post.get("comments_count", 0),
                            "permalink": post.get("permalink", ""),
                            "timestamp": ts
                        })
                except (ValueError, TypeError):
                    pass

        result["recent_posts"] = recent_posts
    except Exception as e:
        print(f"  ✗ Instagram media fetch failed: {e}")
        result["recent_posts"] = []

    return result

def generate_report_with_claude(week_data, prev_week_data, client):
    """Send collected weekly data to Claude API and return a narrative report string."""
    orders_this_week   = week_data.get("orders_this_week", 0)
    total_orders       = week_data.get("orders_count", 0)
    revenue_week_usd   = week_data.get("revenue_this_week_cents", 0) / 100

    ig = week_data.get("instagram") or {}
    ig_reach      = ig.get("reach", 0)
    ig_impressions = ig.get("impressions", 0)
    ig_followers  = ig.get("follower_count", 0)
    ig_posts      = ig.get("recent_posts", [])

    listings = week_data.get("listings") or []
    top_listings  = sorted(listings, key=lambda l: l.get("views_delta", 0), reverse=True)[:5]
    zero_listings = [l for l in listings if l.get("views_delta", 0) == 0]

    prev_revenue_usd  = (prev_week_data.get("revenue_this_week_cents", 0) / 100) if prev_week_data else 0
    prev_ig_reach     = ((prev_week_data.get("instagram") or {}).get("reach", 0)) if prev_week_data else 0
    prev_ig_followers = ((prev_week_data.get("instagram") or {}).get("follower_count", 0)) if prev_week_data else 0

    week_start = week_data.get("week_start", "this week")

    listing_lines = "\n".join(
        f"  - {l['title'][:55]}: +{l.get('views_delta',0)} views, +{l.get('favorites_delta',0)} favs"
        for l in top_listings
    ) if top_listings else "  - No Etsy data available this week (run etsy_auth.py to enable)"

    post_lines = "\n".join(
        f"  - {p['caption_preview'][:60]} — {p['likes']} likes, {p['comments']} comments"
        for p in ig_posts
    ) if ig_posts else "  - No posts this week"

    prompt = f"""You are writing the weekly business report for Rust & Rainbow — a small Etsy print-on-demand shop selling vizsla dog themed products for gay/LGBTQ dog owners. The owner checks this report every Monday morning.

Write as a direct, honest business advisor. Use specific numbers. Be candid about problems; don't just cheerlead. Paragraphs should be 2–4 sentences. No fluff, no filler.

WEEK: {week_start}

ORDERS & REVENUE
- Orders this week: {orders_this_week}
- Revenue this week: ${revenue_week_usd:.2f}
- Revenue last week: ${prev_revenue_usd:.2f}
- Total lifetime orders: {total_orders}

ETSY LISTING ACTIVITY (new views this week vs last week):
{listing_lines}
- Listings with zero new views this week: {len(zero_listings)} of {len(listings)}

INSTAGRAM
- Reach this week: {ig_reach:,} (last week: {prev_ig_reach:,})
- Impressions: {ig_impressions:,}
- Followers: {ig_followers} (was: {prev_ig_followers})
- Posts this week:
{post_lines}

Write the report using EXACTLY these section headers (## markdown):

## Shop Snapshot
2–3 sentences summarising this week's numbers. Compare to last week honestly.

## Story of the Week
The single most important insight from the data — a win, a problem, or a clear pattern. One focused paragraph.

## Etsy Performance
How are listings performing? Which designs gained traction? How many have zero traffic and what does that signal?

## Instagram & Social
How is social performing? Any correlation between posting activity and Etsy view spikes worth noting?

## #1 Focus This Week
One concrete, specific action Ryan should take this week. Not vague advice — a real task.

## Watch Next Week
One metric or event that will tell us whether we're moving in the right direction.

---
*Data pulled {datetime.now().strftime('%Y-%m-%d %H:%M')} from Printify orders API, Etsy listings API, Instagram Graph API. Cumulative view counts; week-over-week deltas calculated from last report. For informational use only.*"""

    try:
        message = client.messages.create(
            model="claude-opus-4-5",   # Update to latest model if needed
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"  ✗ Claude API report generation failed: {e}")
        return None

def optimize_etsy_listings(listing_stats, client):
    """Auto-rewrite titles and tags for zero-traffic listings using Claude, then apply via Etsy API.

    Only runs if ETSY_ACCESS_TOKEN is configured. Limits to 3 rewrites per week
    to avoid over-churning listings. Rewrites are logged in performance_log.
    """
    _etsy_ready = (
        ETSY_ACCESS_TOKEN
        and ETSY_API_KEY
        and ETSY_SHOP_ID
        and not ETSY_ACCESS_TOKEN.startswith("your_")
        and not ETSY_ACCESS_TOKEN.startswith("pending_")
    )
    if not _etsy_ready:
        print("  ⚠ Etsy API not configured — skipping listing optimization.")
        return []

    zero_traffic = [l for l in listing_stats if l.get("views_delta", 0) == 0]
    if not zero_traffic:
        print("  ✓ All listings received views this week — no optimization needed.")
        return []

    print(f"  {len(zero_traffic)} listings with zero new views. Optimizing up to 3...")
    optimizations = []

    etsy_headers = {
        "Authorization": f"Bearer {ETSY_ACCESS_TOKEN}",
        "x-api-key": ETSY_API_KEY,
        "Content-Type": "application/json"
    }

    for listing in zero_traffic[:3]:
        try:
            prompt = f"""You are an Etsy SEO expert for a small print-on-demand shop: Rust & Rainbow.
The shop sells vizsla dog themed merchandise for gay and LGBTQ dog owners.
Products: t-shirts, mugs, hoodies, stickers.

This listing has had ZERO new views this week and needs stronger Etsy search terms.

Current title: {listing['title']}

Etsy SEO rules:
- Title: max 140 chars. Most important keywords first. Comma-separated phrases.
- Tags: exactly 13 tags, each max 20 chars. Multi-word phrases beat single words.
- Prioritise buyer intent: "vizsla gift", "dog dad shirt", "gay dog dad", "vizsla owner gift"
- Mix broad (dog lover gift, dog shirt) with niche (vizsla, hungarian pointer, velcro dog)

Respond with ONLY a JSON object, no other text:
{{
  "title": "rewritten title here",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13"],
  "reason": "one sentence explaining the change"
}}"""

            message = client.messages.create(
                model="claude-haiku-4-5",  # Faster/cheaper for SEO rewrites
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text.strip()

            # Extract JSON (Claude may include surrounding text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print(f"  ✗ Unexpected format from Claude for: {listing['title'][:40]}")
                continue

            opt = json.loads(json_match.group())
            new_title = (opt.get("title") or "").strip()[:140]
            new_tags  = opt.get("tags", [])[:13]
            reason    = opt.get("reason", "")

            if not new_title or len(new_tags) < 5:
                print(f"  ✗ Claude returned incomplete data for: {listing['title'][:40]}")
                continue

            # Apply via Etsy v3 API
            put_resp = requests.put(
                f"https://openapi.etsy.com/v3/application/shops/{ETSY_SHOP_ID}/listings/{listing['listing_id']}",
                headers=etsy_headers,
                json={"title": new_title, "tags": new_tags}
            )
            put_resp.raise_for_status()

            print(f"  ✓ Optimised: {listing['title'][:45]}...")
            print(f"    → {new_title[:60]}...")
            print(f"    Reason: {reason}")

            optimizations.append({
                "listing_id": listing["listing_id"],
                "old_title":  listing["title"],
                "new_title":  new_title,
                "new_tags":   new_tags,
                "reason":     reason
            })
            time.sleep(1)

        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parse error for {listing.get('title','?')[:40]}: {e}")
        except requests.HTTPError as e:
            print(f"  ✗ Etsy PUT failed for {listing.get('title','?')[:40]}: {e.response.status_code} {e.response.text[:120]}")
        except Exception as e:
            print(f"  ✗ Optimisation error for {listing.get('title','?')[:40]}: {e}")

    return optimizations

def build_data_report(week_data, prev_week_data):
    """Build a structured markdown report from raw data for native Claude Code analysis.

    Saved to reports/YYYY-MM-DD.md every Monday.
    Drop the file contents into your Claude Code session for instant narrative — no API key needed.
    """
    orders_this_week  = week_data.get("orders_this_week", 0)
    total_orders      = week_data.get("orders_count", 0)
    revenue_usd       = week_data.get("revenue_this_week_cents", 0) / 100
    prev_revenue_usd  = (prev_week_data.get("revenue_this_week_cents", 0) / 100) if prev_week_data else None
    prev_orders_week  = prev_week_data.get("orders_this_week", 0) if prev_week_data else None

    ig = week_data.get("instagram") or {}
    listings = week_data.get("listings") or []

    lines = []
    lines.append(f"## Business: Rust & Rainbow")
    lines.append(f"## Week: {week_data.get('week_start')} → {week_data.get('week_end')}")
    lines.append(f"## Generated: {week_data.get('generated_at', '')[:10]}\n")

    lines.append("## Orders & Revenue")
    lines.append(f"- Orders this week: **{orders_this_week}**")
    if prev_orders_week is not None:
        delta = orders_this_week - prev_orders_week
        sign = "+" if delta >= 0 else ""
        lines.append(f"- vs last week: {sign}{delta} orders")
    lines.append(f"- Revenue this week: **${revenue_usd:.2f}**")
    if prev_revenue_usd is not None:
        rev_delta = revenue_usd - prev_revenue_usd
        sign = "+" if rev_delta >= 0 else ""
        lines.append(f"- vs last week: {sign}${rev_delta:.2f}")
    lines.append(f"- Lifetime orders: {total_orders}")

    lines.append("\n## Social — Instagram")
    if ig:
        lines.append(f"- Followers: {ig.get('follower_count', 0)}")
        lines.append(f"- Reach: {ig.get('reach', 0):,} | Impressions: {ig.get('impressions', 0):,}")
        posts = ig.get("recent_posts", [])
        lines.append(f"- Posts this week: {len(posts)}")
        for p in posts:
            lines.append(f"  - \"{p['caption_preview'][:70]}\" — {p['likes']} likes")
    else:
        lines.append("- Instagram data unavailable (META_ACCESS_TOKEN may be expired)")

    lines.append("\n## Etsy Listings")
    if listings:
        lines.append("| Listing | Views Δ | Favs Δ |")
        lines.append("|---------|---------|--------|")
        for l in sorted(listings, key=lambda x: x.get("views_delta", 0), reverse=True):
            title = l["title"][:50]
            lines.append(f"| {title} | {l.get('views_delta', 0):+} | {l.get('favorites_delta', 0):+} |")
        zero = sum(1 for l in listings if l.get("views_delta", 0) == 0)
        lines.append(f"\n*{zero} of {len(listings)} listings had zero new views.*")
    else:
        lines.append("*Etsy API not configured — run etsy_auth.py to unlock listing stats + auto-optimisation.*")

    lines.append("\n---")
    lines.append("*Drop this report into Claude Code for narrative analysis and action items.*")
    return "\n".join(lines)

def run_report():
    """Monday morning self-learning loop:
    1. Pull real Printify order data (fixes hardcoded sales=0)
    2. Pull Instagram insights
    3. Pull Etsy listing view deltas
    4. Generate AI narrative report via Claude API  —OR—  structured data report (no API key needed)
    5. Auto-rewrite titles/tags for zero-traffic listings (requires both Claude + Etsy API)
    6. Save report to reports/YYYY-MM-DD.md
    7. Append week's data to performance_log.json for trend tracking
    """
    header("RUST & RAINBOW — WEEKLY REPORT")

    # Claude API is optional — data collection runs regardless.
    # When not configured, the report is formatted for native analysis in Claude Code.
    client = None
    if ANTHROPIC_API_KEY and not ANTHROPIC_API_KEY.startswith("your_"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            print("  Claude API: connected — will generate inline narrative")
        except ImportError:
            print("  ⚠ anthropic package not installed — structured report only")
    else:
        print("  Mode: structured report — drop into Claude Code for instant narrative")

    # Load history for delta calculations and trend context
    perf_log = load_performance_log()
    prev_week_data = perf_log["weeks"][-1] if perf_log["weeks"] else None

    today      = datetime.now()
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")  # Monday
    week_end   = today.strftime("%Y-%m-%d")

    week_data = {
        "week_start":    week_start,
        "week_end":      week_end,
        "generated_at":  today.isoformat(),
    }

    # ── Step 1: Printify orders ──────────────────
    print("\n[1/4] Fetching Printify orders...")
    total_orders, revenue_cents, orders_this_week = get_printify_orders()
    week_data["orders_count"]             = total_orders
    week_data["orders_this_week"]         = orders_this_week
    week_data["revenue_this_week_cents"]  = revenue_cents
    print(f"  Total orders: {total_orders} | This week: {orders_this_week} | Revenue: ${revenue_cents/100:.2f}")

    # ── Step 2: Instagram insights ───────────────
    print("\n[2/4] Fetching Instagram insights...")
    ig_data = get_instagram_insights()
    week_data["instagram"] = ig_data or {}
    if ig_data:
        print(f"  Reach: {ig_data.get('reach', 0):,} | Followers: {ig_data.get('follower_count', 0)} | Posts this week: {len(ig_data.get('recent_posts', []))}")

    # ── Step 3: Etsy listing stats ───────────────
    print("\n[3/4] Fetching Etsy listing stats...")
    listing_stats = get_etsy_listing_stats(prev_week_data)
    week_data["listings"] = listing_stats or []
    if listing_stats:
        zero = sum(1 for l in listing_stats if l.get("views_delta", 0) == 0)
        print(f"  {len(listing_stats)} listings tracked | {zero} with zero new views this week")

    # ── Step 4: Generate report ───────────────────
    if client:
        print("\n[4/4] Generating narrative report with Claude...")
        report_body = generate_report_with_claude(week_data, prev_week_data, client)
        if not report_body:
            print("  ✗ Claude API call failed — falling back to data-only report.")
            report_body = build_data_report(week_data, prev_week_data)
    else:
        print("\n[4/4] Building data report (no Claude API key)...")
        report_body = build_data_report(week_data, prev_week_data)

    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"{week_end}.md"
    report_content = (
        f"---\n"
        f"week: {week_start} to {week_end}\n"
        f"generated: {today.isoformat()}\n"
        f"orders_this_week: {orders_this_week}\n"
        f"revenue_this_week_usd: {revenue_cents/100:.2f}\n"
        f"ai_narrative: {'inline' if client else 'claude-code'}\n"
        f"---\n\n"
        f"# Rust & Rainbow — Week of {week_start}\n\n"
        f"{report_body}\n"
    )
    with open(report_path, "w") as f:
        f.write(report_content)
    print(f"\n  ✓ Report saved → {report_path}")
    print("\n" + "─" * 50)
    print(report_body)
    print("─" * 50)

    # ── Step 5: Auto-optimise zero-traffic listings (requires Claude + Etsy API)
    week_data["optimizations_applied"] = []
    if listing_stats and client:
        print("\n[5/5] Checking for zero-traffic listings to optimise...")
        optimizations = optimize_etsy_listings(listing_stats, client)
        week_data["optimizations_applied"] = optimizations
        if optimizations:
            print(f"  ✓ Applied {len(optimizations)} Etsy optimisation(s)")
    elif listing_stats and not client:
        zero = sum(1 for l in listing_stats if l.get("views_delta", 0) == 0)
        if zero:
            print(f"\n[5/5] {zero} listing(s) have zero views — add ANTHROPIC_API_KEY to enable auto-optimisation.")

    # ── Step 6: Persist weekly data ─────────────
    perf_log["weeks"].append(week_data)
    save_performance_log(perf_log)
    print(f"\n  ✓ Week data appended to performance_log.json ({len(perf_log['weeks'])} weeks tracked)")

    header("WEEKLY REPORT COMPLETE")

# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

def run_generate(num=5):
    header("RUST & RAINBOW — GENERATE + PUBLISH")

    # Generate designs
    designs = generate_designs(num=num)
    if not designs:
        print("No designs generated. Check your Ideogram API key and credits.")
        return

    # Ryan approves
    approved = review_designs(designs)
    if not approved:
        print("No designs approved. Nothing to publish.")
        return

    # Publish approved designs
    log = load_designs_log()
    for design in approved:
        products, cdn_url = upload_to_printify(design)
        design["published_products"] = products
        design["published_at"] = datetime.now().isoformat()
        design["status"] = "published"
        design["sales"] = 0
        # Save permanent Printify CDN URL — used for all social posting.
        # Ideogram URLs are ephemeral (~24h). This URL never expires.
        if cdn_url:
            design["mockup_url"] = cdn_url
            print(f"  ✓ Permanent CDN URL saved: {cdn_url}")
        log.append(design)

    save_designs_log(log)
    header(f"DONE — {len(approved)} design(s) published to Etsy via Printify")

def run_market(auto_confirm=False):
    header("RUST & RAINBOW — MARKETING")
    log = load_designs_log()
    published = [d for d in log if d.get("status") == "published"]

    if not published:
        print("No published designs found. Run --mode generate first.")
        return

    # Rotate through pillars to keep content varied.
    # Step 1: find the pillar posted least recently (never-posted pillars sort first).
    # Step 2: within that pillar, pick the least-recently-posted design.
    # This prevents back-to-back same-pillar posts regardless of how many designs each pillar has.
    from collections import defaultdict
    pillar_last = defaultdict(str)  # pillar -> most recent last_posted across its designs
    for d in published:
        lp = d.get("last_posted") or ""
        if lp > pillar_last[d["pillar"]]:
            pillar_last[d["pillar"]] = lp

    oldest_pillar = min(pillar_last, key=lambda p: pillar_last[p])
    pillar_designs = [d for d in published if d["pillar"] == oldest_pillar]
    pillar_designs.sort(key=lambda d: d.get("last_posted") or "")
    design = pillar_designs[0]
    print(f"Posting: {design['title']} (pillar: {design['pillar']})")

    # Instagram: prefer Printify mockup URL, fall back to Ideogram generation URL.
    # Both are publicly accessible. Ideogram URLs may expire after ~24h so post promptly.
    image_url = get_postable_image_url(design, log=log, log_path=DESIGNS_LOG)
    if not image_url:
        print("  No usable image URL found and local file is missing.")
        print("  Run --mode generate to create new designs with fresh images.")
        return

    print(f"\n  About to post to Instagram, TikTok, and Pinterest:")
    print(f"  Design: {design['title']} ({design['pillar']})")
    print(f"  Image:  {image_url}")

    if not auto_confirm:
        confirm = input("\n  Confirm post to all platforms? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("  Skipped — post cancelled.")
            header("MARKETING DONE")
            return
    else:
        print("  Auto-confirmed (--yes flag set).")

    # Instagram
    post_to_instagram(design, image_url)

    # Pinterest: full caption with hashtags (no limit)
    pinterest_caption = build_caption(design) + " #rustandrainbow"
    post_to_pinterest(image_url, pinterest_caption, design)

    # TikTok: title is capped at 90 chars — pure hook, no hashtags.
    # All hashtags go into tiktokSettings.description (4000 char limit, separate field).
    hook = build_caption(design).split("\n\n")[0]  # e.g. "Two dads. One vizsla. Zero regrets. 🌈🐕"
    tiktok_title = hook[:90]
    tiktok_description = build_tiktok_description(design)
    post_to_tiktok(image_url, tiktok_title, tiktok_description)

    # Stamp last_posted so this design sorts to the back of the queue next run
    from datetime import datetime, timezone
    design["last_posted"] = datetime.now(timezone.utc).isoformat()
    save_designs_log(log)

    header("MARKETING DONE")

def main():
    parser = argparse.ArgumentParser(description="Rust & Rainbow Automation Agent")
    parser.add_argument("--mode", choices=["generate", "market", "monitor", "report", "all"], required=True)
    parser.add_argument("--num", type=int, default=5, help="Number of designs to generate")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompts (for automated/unattended runs)")
    args = parser.parse_args()

    print("""
 ██████╗ ██╗   ██╗███████╗████████╗     ██╗
 ██╔══██╗██║   ██║██╔════╝╚══██╔══╝    ███║
 ██████╔╝██║   ██║███████╗   ██║       ╚██║
 ██╔══██╗██║   ██║╚════██║   ██║        ██║
 ██║  ██║╚██████╔╝███████║   ██║        ██║
 ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝        ╚═╝
    Rust & Rainbow Automation Agent
    """)

    if args.mode in ("generate", "all"):
        check_env("generate")
        run_generate(num=args.num)
    if args.mode in ("market", "all"):
        check_env("market")
        run_market(auto_confirm=args.yes)
    if args.mode in ("monitor", "all"):
        check_env("monitor")
        run_monitor()
    if args.mode == "report":
        check_env("report")
        run_report()

if __name__ == "__main__":
    main()

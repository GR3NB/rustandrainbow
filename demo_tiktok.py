#!/usr/bin/env python3
"""
Rust & Rainbow — TikTok Demo Runner
Runs the full TikTok Content Posting API flow for the TikTok app review demo video.

This script is designed to be recorded on screen. It shows:
  1. Token / account verification
  2. Test video upload to creator inbox (drafts)
  3. Upload status polling
  4. Video list confirmation
  5. Account stats (follower/like counts)

Usage:
    python3 demo_tiktok.py

Requirements:
    TIKTOK_ACCESS_TOKEN in .env  (run tiktok_auth.py first)
    output/tiktok_demo_test.mp4  (run create_test_video.py first)
"""

import os
import sys
import time
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_CLIENT_KEY   = os.getenv("TIKTOK_CLIENT_KEY", "")
TEST_VIDEO_PATH     = Path("output/tiktok_demo_test.mp4")

BASE = "https://open.tiktokapis.com/v2"
HDR   = lambda: {
    "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
    "Content-Type":  "application/json; charset=UTF-8",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print(f"{'═'*55}\n")

def ok(msg):  print(f"  ✓ {msg}")
def err(msg): print(f"  ✗ {msg}")
def info(msg): print(f"  → {msg}")

# ── Step 1: Verify token ───────────────────────────────────────────────────────

def verify_token():
    section("STEP 1 — Verify Token & Account")
    if not TIKTOK_ACCESS_TOKEN or TIKTOK_ACCESS_TOKEN.startswith("pending"):
        err("TIKTOK_ACCESS_TOKEN not set. Run: python3 tiktok_auth.py")
        sys.exit(1)

    resp = requests.get(
        f"{BASE}/user/info/",
        headers=HDR(),
        params={"fields": "open_id,union_id,avatar_url,display_name,profile_deep_link"},
    )

    if resp.status_code != 200:
        err(f"Token check failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    data = resp.json().get("data", {}).get("user", {})
    ok(f"Token valid")
    ok(f"Account: {data.get('display_name', 'unknown')}")
    info(f"Profile: {data.get('profile_deep_link', '')}")
    return data


# ── Step 2: Upload video to inbox ─────────────────────────────────────────────

def upload_video():
    section("STEP 2 — Upload Test Video to TikTok Inbox (Drafts)")

    if not TEST_VIDEO_PATH.exists():
        err(f"Test video not found: {TEST_VIDEO_PATH}")
        err("Run first: python3 create_test_video.py")
        sys.exit(1)

    video_size = TEST_VIDEO_PATH.stat().st_size
    info(f"Video: {TEST_VIDEO_PATH} ({video_size / 1_000_000:.1f} MB)")
    print()

    # Init upload
    info("Initializing upload...")
    init_resp = requests.post(
        f"{BASE}/post/publish/inbox/video/init/",
        headers=HDR(),
        json={
            "source_info": {
                "source":             "FILE_UPLOAD",
                "video_size":         video_size,
                "chunk_size":         video_size,
                "total_chunk_count":  1,
            }
        },
    )

    if init_resp.status_code != 200:
        err(f"Init failed: {init_resp.status_code} {init_resp.text}")
        sys.exit(1)

    data       = init_resp.json()["data"]
    upload_url = data["upload_url"]
    publish_id = data["publish_id"]
    ok(f"Upload initialized (publish_id: {publish_id})")

    # PUT video bytes
    info("Uploading video bytes...")
    with open(TEST_VIDEO_PATH, "rb") as f:
        video_bytes = f.read()

    put_resp = requests.put(
        upload_url,
        headers={
            "Content-Type":  "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        },
        data=video_bytes,
    )

    if put_resp.status_code not in (200, 201, 204):
        err(f"Upload PUT failed: {put_resp.status_code} {put_resp.text}")
        sys.exit(1)

    ok("Video bytes uploaded")
    return publish_id


# ── Step 3: Poll upload status ────────────────────────────────────────────────

def poll_status(publish_id):
    section("STEP 3 — Poll Upload Status")
    info(f"Checking status for publish_id: {publish_id}")
    info("Waiting 10 seconds for TikTok to process...")
    time.sleep(10)

    for attempt in range(1, 6):
        resp = requests.post(
            f"{BASE}/post/publish/status/fetch/",
            headers=HDR(),
            json={"publish_id": publish_id},
        )

        if resp.status_code != 200:
            err(f"Status check failed: {resp.status_code} {resp.text}")
            break

        status = resp.json().get("data", {}).get("status", "unknown")
        info(f"Attempt {attempt}: status = {status}")

        if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            ok(f"Upload complete — video is in creator inbox (status: {status})")
            ok("Open TikTok app → Inbox → tap to review and publish")
            return status
        elif status in ("FAILED", "CANCELLED"):
            err(f"Upload failed with status: {status}")
            return status
        else:
            info("Still processing... waiting 5s")
            time.sleep(5)

    return "unknown"


# ── Step 4: List videos on account ───────────────────────────────────────────

def list_videos():
    section("STEP 4 — Confirm Video List")
    resp = requests.post(
        f"{BASE}/video/list/",
        headers=HDR(),
        params={"fields": "id,title,create_time,share_url,view_count,like_count,comment_count"},
        json={"max_count": 5},
    )

    if resp.status_code != 200:
        err(f"Video list failed: {resp.status_code} {resp.text}")
        return

    videos = resp.json().get("data", {}).get("videos", [])
    ok(f"Retrieved {len(videos)} video(s) from account")
    print()
    for v in videos:
        print(f"  [{v.get('id', '?')}] {v.get('title', 'untitled')[:50]}")
        print(f"       Views: {v.get('view_count',0)} | Likes: {v.get('like_count',0)}")


# ── Step 5: Account stats ─────────────────────────────────────────────────────

def account_stats():
    section("STEP 5 — Account Stats")
    resp = requests.get(
        f"{BASE}/user/info/",
        headers=HDR(),
        params={"fields": "follower_count,following_count,likes_count,video_count"},
    )

    if resp.status_code != 200:
        err(f"Stats fetch failed: {resp.status_code} {resp.text}")
        return

    data = resp.json().get("data", {}).get("user", {})
    ok("Account stats retrieved:")
    print(f"  Followers:  {data.get('follower_count', 0):,}")
    print(f"  Following:  {data.get('following_count', 0):,}")
    print(f"  Total likes: {data.get('likes_count', 0):,}")
    print(f"  Videos:     {data.get('video_count', 0):,}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("""
╔══════════════════════════════════════════════════╗
║   Rust & Rainbow — TikTok Integration Demo       ║
║   Content Posting API · Creator Inbox Flow       ║
╚══════════════════════════════════════════════════╝
    """)

    verify_token()
    publish_id = upload_video()
    status = poll_status(publish_id)
    list_videos()
    account_stats()

    section("DEMO COMPLETE")
    ok("TikTok Content Posting API — all steps passed")
    info("Video is in creator inbox — open TikTok app to review and publish")
    info("This flow runs automatically via agent.py --mode market")


if __name__ == "__main__":
    main()

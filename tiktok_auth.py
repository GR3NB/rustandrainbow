#!/usr/bin/env python3
"""
TikTok OAuth 2.0 + PKCE flow for Rust & Rainbow
Run this once after TikTok approves your app to get your access + refresh tokens.

Usage:
    python3 tiktok_auth.py

How it works:
    1. Script opens TikTok authorization page in your browser
    2. Log in as @rustandrainbowco and approve the app
    3. TikTok redirects to your GitHub Pages URL with ?code=... in the address bar
    4. Copy the full URL from the address bar and paste it here
    5. Script exchanges the code for tokens and writes them to .env

Requirements:
    TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET must be set in .env
"""

import base64
import hashlib
import os
import secrets
import sys
import urllib.parse
import webbrowser

import requests
from dotenv import load_dotenv, set_key

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

REDIRECT_URI  = "https://rustandrainbow.github.io/rustandrainbow/"
SCOPES        = "user.info.basic,user.info.profile,user.info.stats,video.upload,video.list"
AUTH_URL_BASE = "https://www.tiktok.com/v2/auth/authorize/"
ENV_FILE      = os.path.join(os.path.dirname(__file__), ".env")

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# ── PKCE helpers ──────────────────────────────────────────────────────────────

def generate_code_verifier() -> str:
    return secrets.token_urlsafe(48)

def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

# ── Token exchange ────────────────────────────────────────────────────────────

def exchange_code(code, verifier, client_key, client_secret):
    resp = requests.post(TOKEN_URL, data={
        "client_key":     client_key,
        "client_secret":  client_secret,
        "code":           code,
        "grant_type":     "authorization_code",
        "redirect_uri":   REDIRECT_URI,
        "code_verifier":  verifier,
    })
    resp.raise_for_status()
    return resp.json()

# ── .env updater ──────────────────────────────────────────────────────────────

def update_env(key, value):
    set_key(ENV_FILE, key, value, quote_mode="never")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    client_key    = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

    if not client_key or client_key.startswith("pending"):
        print("[ERROR] TIKTOK_CLIENT_KEY not set in .env.")
        print("Get it from: https://developers.tiktok.com/app/7638050043181959175")
        sys.exit(1)
    if not client_secret or client_secret.startswith("pending"):
        print("[ERROR] TIKTOK_CLIENT_SECRET not set in .env.")
        sys.exit(1)

    verifier  = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    state     = secrets.token_urlsafe(16)

    params = {
        "client_key":            client_key,
        "response_type":         "code",
        "scope":                 SCOPES,
        "redirect_uri":          REDIRECT_URI,
        "state":                 state,
        "code_challenge":        challenge,
        "code_challenge_method": "S256",
    }
    auth_url = AUTH_URL_BASE + "?" + urllib.parse.urlencode(params)

    print("\n── TikTok OAuth Setup ───────────────────────────────────────────")
    print("Opening your browser to TikTok authorization page...")
    print("Log in as @rustandrainbowco and approve the app.\n")
    print("After approving, TikTok will redirect to your GitHub Pages URL.")
    print("The address bar will look like:")
    print("  https://rustandrainbow.github.io/rustandrainbow/?code=XXXX&state=YYYY\n")
    print("Copy that full URL and paste it below.\n")

    webbrowser.open(auth_url)

    # Ask Ryan to paste the redirect URL
    redirect_url = input("Paste the full redirect URL here: ").strip()

    # Extract code and state from the pasted URL
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        params_back = dict(urllib.parse.parse_qsl(parsed.query))
    except Exception:
        print("[ERROR] Could not parse that URL. Copy the full address bar contents.")
        sys.exit(1)

    if "error" in params_back:
        print(f"[ERROR] TikTok returned an error: {params_back.get('error')} — {params_back.get('error_description', '')}")
        sys.exit(1)

    if "code" not in params_back:
        print("[ERROR] No 'code' found in that URL. Make sure you copied the full address bar URL after approving.")
        sys.exit(1)

    if params_back.get("state") != state:
        print("[ERROR] State mismatch — possible CSRF or expired session. Run the script again.")
        sys.exit(1)

    code = params_back["code"]
    print("\nCode received. Exchanging for tokens...")

    try:
        tokens = exchange_code(code, verifier, client_key, client_secret)
    except requests.HTTPError as e:
        print(f"\n[ERROR] Token exchange failed: {e}")
        print("Response:", e.response.text)
        sys.exit(1)

    # TikTok wraps tokens inside a "data" key
    token_data    = tokens.get("data", tokens)
    access_token  = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in    = token_data.get("expires_in", "unknown")
    open_id       = token_data.get("open_id", "")

    if not access_token:
        print("\n[ERROR] No access token in response:", tokens)
        sys.exit(1)

    update_env("TIKTOK_ACCESS_TOKEN", access_token)
    if refresh_token:
        update_env("TIKTOK_REFRESH_TOKEN", refresh_token)
    if open_id:
        update_env("TIKTOK_OPEN_ID", open_id)

    print("\n── Success ───────────────────────────────────────────────────────")
    print("  TIKTOK_ACCESS_TOKEN  → written to .env")
    if refresh_token:
        print("  TIKTOK_REFRESH_TOKEN → written to .env")
    if open_id:
        print(f"  TIKTOK_OPEN_ID       → {open_id}")
    hrs = int(expires_in) // 3600 if isinstance(expires_in, int) else "?"
    print(f"  Expires in: {expires_in}s (~{hrs}h)")
    print("\nRun next: python3 demo_tiktok.py")

if __name__ == "__main__":
    main()

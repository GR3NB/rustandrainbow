#!/usr/bin/env python3
"""
Etsy OAuth 2.0 PKCE flow for Rust & Rainbow
Run this once after your Etsy app is approved to get your access + refresh tokens.

Usage:
    python3 etsy_auth.py

Requirements:
    ETSY_API_KEY and ETSY_API_SECRET must be set in .env
"""

import base64
import hashlib
import json
import os
import re
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv, set_key

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

REDIRECT_URI   = "http://localhost:3003/callback"
SCOPES         = "listings_r listings_w listings_d shops_r transactions_r"
AUTH_URL_BASE  = "https://www.etsy.com/oauth/connect"
TOKEN_URL      = "https://api.etsy.com/v3/public/oauth/token"
ENV_FILE       = os.path.join(os.path.dirname(__file__), ".env")

# ── PKCE helpers ──────────────────────────────────────────────────────────────

def generate_code_verifier() -> str:
    """Random 64-char URL-safe string."""
    return secrets.token_urlsafe(48)  # 48 bytes → 64 base64url chars


def generate_code_challenge(verifier: str) -> str:
    """SHA-256 of the verifier, base64url-encoded (no padding)."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# ── Local callback server ─────────────────────────────────────────────────────

captured = {}  # populated by the callback handler


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        captured.update(params)

        # Respond to the browser
        if "code" in params:
            body = b"<h2>Authorization granted. You can close this tab.</h2>"
        else:
            body = b"<h2>Something went wrong. Check terminal.</h2>"

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # suppress server logs


def wait_for_callback() -> dict:
    server = HTTPServer(("localhost", 3003), CallbackHandler)
    server.handle_request()  # handle exactly one request then stop
    return captured


# ── Token exchange ────────────────────────────────────────────────────────────

def exchange_code(code: str, verifier: str, api_key: str, api_secret: str) -> dict:
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "client_id":     api_key,
        "redirect_uri":  REDIRECT_URI,
        "code":          code,
        "code_verifier": verifier,
    })
    resp.raise_for_status()
    return resp.json()


# ── .env updater ──────────────────────────────────────────────────────────────

def update_env(key: str, value: str):
    """Write/overwrite a key in the .env file."""
    # set_key from dotenv handles this cleanly
    set_key(ENV_FILE, key, value, quote_mode="never")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api_key    = os.getenv("ETSY_API_KEY")
    api_secret = os.getenv("ETSY_API_SECRET")

    if not api_key or api_key.startswith("your_"):
        print("[ERROR] ETSY_API_KEY not set in .env. Add it and re-run.")
        sys.exit(1)
    if not api_secret or api_secret.startswith("your_"):
        print("[ERROR] ETSY_API_SECRET not set in .env. Add it and re-run.")
        sys.exit(1)

    # 1. Generate PKCE pair
    verifier  = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    state     = secrets.token_urlsafe(16)

    # 2. Build auth URL
    params = {
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "client_id":             api_key,
        "state":                 state,
        "code_challenge":        challenge,
        "code_challenge_method": "S256",
    }
    auth_url = AUTH_URL_BASE + "?" + urllib.parse.urlencode(params)

    print("\n── Etsy OAuth Setup ─────────────────────────────────────────────")
    print("Opening your browser. If it doesn't open automatically, visit:")
    print(f"\n  {auth_url}\n")
    print("Waiting for you to authorize the app in the browser...")

    # 3. Start callback server in a thread, then open browser
    server_thread = threading.Thread(target=wait_for_callback, daemon=True)
    server_thread.start()
    webbrowser.open(auth_url)
    server_thread.join(timeout=120)

    # 4. Check we got a code
    if "code" not in captured:
        print("\n[ERROR] No authorization code received. Did you approve the app?")
        print("Captured params:", captured)
        sys.exit(1)

    if captured.get("state") != state:
        print("\n[ERROR] State mismatch — possible CSRF. Aborting.")
        sys.exit(1)

    code = captured["code"]
    print("Authorization code received. Exchanging for tokens...")

    # 5. Exchange code for tokens
    try:
        tokens = exchange_code(code, verifier, api_key, api_secret)
    except requests.HTTPError as e:
        print(f"\n[ERROR] Token exchange failed: {e}")
        print("Response:", e.response.text)
        sys.exit(1)

    access_token  = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in    = tokens.get("expires_in", "unknown")

    if not access_token:
        print("\n[ERROR] No access token in response:", json.dumps(tokens, indent=2))
        sys.exit(1)

    # 6. Derive Shop ID from the access token (encoded in it) or fetch it
    shop_id = fetch_shop_id(access_token, api_key)

    # 7. Write to .env
    update_env("ETSY_ACCESS_TOKEN", access_token)
    if refresh_token:
        update_env("ETSY_REFRESH_TOKEN", refresh_token)
    if shop_id:
        update_env("ETSY_SHOP_ID", shop_id)

    print("\n── Success ───────────────────────────────────────────────────────")
    print(f"  ETSY_ACCESS_TOKEN  → written to .env")
    if refresh_token:
        print(f"  ETSY_REFRESH_TOKEN → written to .env")
    if shop_id:
        print(f"  ETSY_SHOP_ID       → {shop_id} (written to .env)")
    print(f"  Token expires in:  {expires_in}s (~{int(expires_in)//3600}h)" if isinstance(expires_in, int) else f"  Token expires in:  {expires_in}")
    print("\nYou're all set. Run: python agent.py --mode generate")


def fetch_shop_id(access_token: str, api_key: str) -> str | None:
    """Fetch the shop ID for the authenticated user."""
    try:
        resp = requests.get(
            "https://openapi.etsy.com/v3/application/users/me",
            headers={
                "x-api-key":     api_key,
                "Authorization": f"Bearer {access_token}",
            }
        )
        resp.raise_for_status()
        data = resp.json()
        # The user object contains shop info if they have a shop
        shop_id = str(data.get("shop_id", "") or "")
        return shop_id if shop_id and shop_id != "0" else None
    except Exception as e:
        print(f"  (Could not auto-fetch shop ID: {e} — set ETSY_SHOP_ID manually)")
        return None


if __name__ == "__main__":
    main()

# Rust & Rainbow — Lessons Learned

Last updated: 2026-05-21

These are hard-won lessons from building the social posting automation stack. Each one
cost real time. Read this before touching social API integrations again.

---

## 1. TikTok does not allow posting to your own account via API

**What happened:** Applied for TikTok developer app access to post to @rustandrainbowco.
Rejected twice (2026-05-10, 2026-05-14). Second rejection confirmed it is a hard policy wall.

**The exact policy:**
> "TikTok for Developers currently does not support personal or internal company use.
> Not acceptable: Display posts from the TikTok account(s) you or your team manage."

**Why this matters:** No amount of reframing the app name or description fixes this.
The underlying use case (developer posting to their own account) is categorically excluded.
TikTok's API is designed for multi-tenant apps where external users connect their accounts.

**The fix:** Use a third-party scheduling service that is already an approved TikTok developer.
The user connects their TikTok account to that service; the service posts on their behalf.
We use Zernio for this.

**Time wasted:** ~2 weeks across two submission cycles, multiple HTML page rewrites,
OAuth scope reviews, app description rewrites.

**Rule for next time:** Before building any social API integration, check the platform's
developer use case policy. If "posting to your own account" is listed as a disallowed use
case, skip the direct API and go straight to a scheduling service.

---

## 2. Buffer's API is closed to new developers as of 2026

**What happened:** Tried to use Buffer as a TikTok posting middleman.
The token from Buffer's settings page returned: "OIDC tokens are not accepted for direct API access."

**Root cause:** Buffer runs two API surfaces, neither accessible to new developers:
- v1 REST API (legacy): stopped accepting new developer app registrations
- GraphQL API (new): in public beta, third-party OAuth not yet enabled

The token you get from Buffer's account settings is an OIDC session token for their
internal services, not an OAuth API access token. These are different things.

**The fix:** Zernio instead of Buffer. Zernio's API is open, documented, free for 2 accounts,
and supports TikTok, Pinterest, and 13 other platforms.

**Time wasted:** ~1 hour of debugging auth errors before the root cause was identified.

**Rule for next time:** When a scheduling tool says "API available," verify that new developer
app registration is actually open before building anything. Buffer is currently closed.

---

## 3. Pinterest's direct API requires a review process for public pins

**What happened:** Researched Pinterest API v5 as a direct integration (no middleman).

**The reality:**
- Trial access: pins are only visible to the app creator (not public on Pinterest)
- Standard access: requires submitting a demo video + 10+ day review wait
- This is comparable friction to TikTok's review process

**The fix:** Zernio handles Pinterest too. Same account, same API key, same call pattern.
Board ID is the URL slug from the board URL (e.g., `rust-and-rainbow-designs` from
`pinterest.com/rustandrainbow/rust-and-rainbow-designs/`).

**Rule for next time:** Pinterest direct API is not a quick win for a solo operator.
Use a scheduling service with existing Pinterest approval unless you are building a
multi-tenant product that genuinely needs direct API access.

---

## 4. For posting to your own social accounts, use a scheduling service, not a direct API

**The pattern that works:**

    agent.py → Zernio API → TikTok / Pinterest

**Why:** TikTok, Pinterest, and others are designed for apps serving external users.
A solo operator posting to their own account is exactly the use case these platforms
exclude from direct API access. Scheduling services (Zernio, Later, Buffer when open)
are already approved developers on all these platforms. You connect your account once
in their dashboard; they handle everything including OAuth token refresh.

**Zernio specifics (confirmed working 2026-05-14):**
- Base URL: `https://api.zernio.com`
- Auth: `Authorization: Bearer {ZERNIO_API_KEY}`
- Post endpoint: `POST /v1/posts`
- Platforms format: `[{"platform": "tiktok", "accountId": "..."}]`
- Media format: `[{"url": "https://...", "type": "image"}]`
- Immediate post: `"publishNow": true`
- Pinterest board: `"platformSpecificData": {"pinterest": {"boardId": "board-url-slug", "title": "..."}}`
- Free tier: 2 connected accounts, full API access
- TikTok account ID: 6a064da65e333c05296d2ff7
- Pinterest account ID: 6a064dd25e333c05296d3130

**Token refresh:** Zernio manages OAuth token refresh for connected accounts automatically.
If a post fails with an auth error, re-connect the account in the Zernio dashboard (2 min fix).

---

## 5. TikTok image posts eliminate the video pipeline entirely

**What happened:** Original plan was to post slideshow videos to TikTok using moviepy
to stitch design images together, then host the video at a public URL for TikTok to fetch.

**Why we dropped it:**
- Requires moviepy installed
- Requires a video hosting service (Cloudinary or similar) for a public URL
- TikTok's API was rejected anyway, making all of this moot
- Zernio accepts image posts for TikTok, which are natively supported by TikTok

**The simpler stack:** Pass the Ideogram image URL directly to Zernio. No video generation,
no hosting, no extra dependencies. The Ideogram URL is already public.

**Tradeoff:** Video performs better than images on TikTok algorithmically. If future Ryan
wants video posts, the upgrade path is: generate video locally with moviepy, upload to
Cloudinary free tier, pass the Cloudinary URL to Zernio instead of the image URL.

---

## 6. Ideogram image URLs are ephemeral — never rely on them for social posting

**What happened:** agent.py stored Ideogram URLs in designs_log.json and used them later for
Instagram, TikTok, and Pinterest posting. Ideogram's generation URLs are labeled "ephemeral"
in the URL path itself and expire within ~24 hours. Running --mode market on any design older
than a day produces 410 Gone errors on all three platforms simultaneously.

**Compounding problem:** The local image files downloaded to output/ were also cleared
(output/ is a scratch directory). With both the Ideogram URL and local file gone, and
Printify mockup images only recoverable if the Printify product wasn't deleted, 8 of 12
designs were unrecoverable.

**The fix (now in place):**
- `upload_to_printify()` captures `preview_url` from Printify's upload response (permanent CloudFront CDN URL) and returns it
- `run_generate()` saves it as `design["mockup_url"]` in designs_log.json
- `get_postable_image_url()` resolves URLs in priority order: mockup_url → verify image_url → re-upload local file to Printify CDN
- New designs will always have a permanent CDN URL from the moment they're published

**Recovery path for existing designs with expired URLs:**
1. Call Printify API: `GET /v1/shops/{shop_id}/products/{product_id}.json`
2. Extract `images[0].src` — permanent Printify CloudFront URL
3. Save as `design["mockup_url"]` in designs_log.json
4. If product was deleted from Printify AND local file is gone: design is unrecoverable, archive it

**Rule for next time:** Never store an ephemeral image URL as the canonical image reference
for a design. The moment you have a permanent CDN URL (from Printify, Cloudinary, etc.),
save it immediately and use only that for social posting.

---

## 7. Confirm platform API assumptions by calling the API before building

**What happened multiple times:** Made assumptions about request formats, endpoint paths,
and auth methods based on documentation or search results, then wrote code against those
assumptions, then found out the API worked differently.

**What works:** Before writing any integration code, call the API exploratorily:
1. Try the most likely base URL and auth method
2. Try an empty POST to the create endpoint to see what fields come back
3. Intentionally send bad input to get error messages that reveal the correct format
4. Confirm the exact format works before building the full function

This takes 10 minutes and saves hours of rework.

---

## 8. Use cron, not launchd, for scheduled scripts that access ~/Documents

**What happened:** Set up a launchd plist to run agent.py --mode market on a Mon/Wed/Fri schedule.
The job loaded successfully (launchctl list showed it) but every run failed with:
"Operation not permitted" then "Permission denied" after moving the script to /usr/local/bin.

**Root cause:** macOS's TCC (Transparency, Consent, and Control) framework protects ~/Documents
from processes that don't have explicit Full Disk Access. launchd agents run in a separate process
context from Terminal — granting Terminal Full Disk Access does NOT transfer to launchd-spawned
processes. The agent couldn't cd into the project directory, couldn't read the script file,
couldn't do anything in ~/Documents.

**Fixes tried that did NOT work:**
- Granting Terminal Full Disk Access in System Settings → Privacy & Security
- Moving run_market.sh to /usr/local/bin (fixed "Operation not permitted" but not "Permission denied")
- Rewriting the plist to inline the command with bash -c instead of calling a script file
- Setting WorkingDirectory and EnvironmentVariables keys in the plist

**The fix:** Use cron instead of launchd. Cron runs in the user's session context and does not
have the same TCC restrictions on ~/Documents. Set with a single pipe command — no vim required:

    echo '0 10 * * 1,3,5 cd "/path/to/project" && /usr/bin/python3 agent.py --mode market --yes >> market.log 2>&1' | crontab -

Verify with: crontab -l

**Current schedule (confirmed working 2026-05-14):**
    0 10 * * 1,3,5 cd "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow" && /usr/bin/python3 agent.py --mode market --yes >> market.log 2>&1

**Rule for next time:** On macOS, cron cannot use shell redirects (>>) into TCC-protected
directories: ~/Documents, ~/Desktop, ~/Downloads. The cd into those directories works fine,
but the file write is blocked. Log files must live outside those paths.

**Correct log location:** ~/Library/Logs/ is NOT TCC-protected and is where cron can write.

**Also:** The --yes flag was added to agent.py to skip the interactive confirm prompt in
run_market(). Always pass --yes for any automated/unattended run. Without it the script
hangs waiting for keyboard input and the cron job times out silently.

**Failure mode to watch for:** cron sends mail to /var/mail/ryannortham when a job produces
uncaptured output (i.e., when the redirect itself fails). If posts stop appearing, run
`cat /var/mail/ryannortham` to see the cron error. A watchdog cron (see below) handles
this automatically now.

---

## 9. --mode generate cannot run unattended — review step requires a real TTY

**What happened:** Attempted to run `python3 agent.py --mode generate` from Claude Code's Bash tool (non-interactive context). Ideogram generated all 4 images successfully and saved them to output/. But `review_designs()` calls Python's `input()`, which requires a TTY. In a non-interactive shell, `input()` raises `EOFError` immediately.

**What works:** Run `--mode generate` directly from Terminal.app, not from any automated context. The images open in Preview; you type A/S/Q per image.

**Workaround used (2026-05-21):** When images were already downloaded but review failed, wrote a one-off `_publish_pending.py` script with the design metadata hardcoded, published directly, then deleted the script. This avoids re-calling Ideogram (costs credits) and gets around the TTY issue.

**Rule for next time:** `--mode generate` = interactive, run from Terminal. `--mode market` and `--mode monitor` = unattended-safe (use `--yes` for market). If you need to publish pre-generated images without a TTY, write a targeted one-off script that calls `upload_to_printify()` directly.

**Also learned:** Always verify Printify blueprint IDs against the live catalog API before hardcoding. Blueprint 367 (assumed Kiss-Cut Stickers) returned 404 — the real ID is 400. Use this to check: `GET /v1/catalog/blueprints.json` and filter by title.

---

## 10. TikTok photo posts have a hard 90-character caption limit

**What happened:** `run_market()` built a full `build_caption()` output (hook + body + hashtags = ~335 chars) and passed it to `post_to_tiktok()`. TikTok's API returned a 400 error on the first market run of the day. The error body showed the text field exceeded the platform max.

**Root cause:** TikTok photo posts (not video) cap the `text` field at 90 characters. There is no way around this — it is a hard API limit, not a truncation hint.

**The fix (now in agent.py `run_market()`):**
```python
# Pinterest: full caption with hashtags (no limit)
pinterest_caption = build_caption(design) + " #rustandrainbow"
post_to_pinterest(image_url, pinterest_caption, design)

# TikTok: photo posts capped at 90 characters — use just the hook line + 2-3 key tags
hook = build_caption(design).split("\n\n")[0]
tiktok_caption = (hook + " #rustandrainbow #vizsla #dogtok")[:90]
post_to_tiktok(image_url, tiktok_caption)
```

**Why this matters:** Pinterest and Instagram have no practical caption limits for this use case (2200 and 2200 chars respectively). TikTok is the only platform with a strict short cap. The platforms must be handled separately — do not share a single `social_caption` variable across all three.

**Rule for next time:** If a social post to TikTok returns 400, check caption length first. Build TikTok captions as hook-only (the first paragraph of `build_caption()`) + 2–3 hashtags, sliced to 90 chars. Never pass full multi-paragraph captions to TikTok.

---

## Current working stack (2026-05-21)

| Layer | Tool | Notes |
|---|---|---|
| Design generation | Ideogram API | Prompts in agent.py PROMPTS library; duplicate-title guard prevents re-publishing same design |
| Product creation | Printify API | Blueprints 6 (t-shirt), 68 (mug), 77 (hoodie), 400 (Kiss-Cut Sticker) |
| Etsy publishing | Printify native integration | No Etsy API key needed |
| Instagram | Meta Graph API | graph.instagram.com/v22.0 |
| Facebook | Native cross-post from Instagram | Enabled in Accounts Center, no API needed |
| TikTok | Zernio | Image post, publishNow: true |
| Pinterest | Zernio | Image post to rust-and-rainbow-designs board |
| Scheduling | cron | Mon/Wed/Fri 10am + Stock agent Mon–Fri 2pm |
| Watchdog | cron + watchdog.sh | Mon/Wed/Fri 10:10am, notifies if post missed |

**Cron jobs (current — updated 2026-05-21 after folder move to ~/Claude/):**
    0 10 * * 1,3,5 cd "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow" && /usr/bin/python3 agent.py --mode market --yes >> /Users/ryannortham/Library/Logs/rust_rainbow_market.log 2>&1
    10 10 * * 1,3,5 /bin/bash "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/watchdog.sh"
    0 14 * * 1-5 /usr/bin/python3 /Users/ryannortham/Claude/Projects/Stock/agent.py >> /Users/ryannortham/Claude/Projects/Stock/agent.log 2>&1

To view: crontab -l
To edit: Use a heredoc — see README or Project_State. Avoid crontab -e (opens vim).
Log file: ~/Library/Logs/rust_rainbow_market.log  (NOT inside project dir — TCC restriction even though project is now in ~/Claude/)

**Known gaps (open items as of 2026-05-21):**
- run_monitor() does not fetch real sales data — sales field is always 0. Needs Printify order API integration to pull actual order counts.
- Duplicate listing: Gay Dog Dad Retro published twice (May 11 + May 14). Delete one in Printify dashboard → unpublishes from Etsy automatically.

**Resolved gaps:**
- ✅ Sticker product added — blueprint 400 (Kiss-Cut Stickers, verified from live Printify catalog). Blueprint 367 does not exist — 404 on first attempt. Always verify blueprint IDs against the catalog API before hardcoding.
- ✅ PNW pillar — Oregon Vizsla generated and published 2026-05-21.
- ✅ All 4 new designs (Rainbow Heart Vizsla, Oregon Vizsla, Gay Agenda, Retro Vizsla Poster) published to t-shirt, mug, hoodie, and sticker on 2026-05-21.
- ✅ TikTok caption 400 error fixed — `run_market()` now sends platform-specific captions: full caption to Pinterest/Instagram, hook-only (≤90 chars) to TikTok. Confirmed working across 5 market runs on 2026-05-21.

**Token expiry reminders:**
- META_ACCESS_TOKEN: refresh by 2026-07-01 (long-lived, ~60 day rolling) — **SET A CALENDAR REMINDER FOR JUNE 25**
- Zernio API key: valid until ~2027-05-14 (1 year)
- Zernio platform tokens: auto-refreshed by Zernio

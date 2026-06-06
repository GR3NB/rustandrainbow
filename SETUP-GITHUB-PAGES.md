# GitHub Pages Setup — Privacy Policy & Terms of Service

**Why this matters:** TikTok and Meta will not approve your app without publicly hosted privacy + terms URLs. GitHub Pages is free, takes 10 minutes, and gives you URLs both platforms accept.

**Tradeoff risk:** A `github.io` URL looks slightly less polished than a real domain (e.g., `rustandrainbow.co`). Some reviewers may treat it as "hobbyist." If your TikTok app gets rejected with a "verify your business identity" or "non-business URL" reason, that's the signal to upgrade to a custom domain via Carrd or Namecheap. For first submission, GitHub Pages is fine.

---

## What you'll end up with

Two public URLs under the GR3NB organization:
- `https://gr3nb.github.io/rust-and-rainbow/privacy.html`
- `https://gr3nb.github.io/rust-and-rainbow/terms.html`

Both render the markdown files I already created in `Rust & Rainbow/legal/`.

---

## Step 1 — GitHub org setup (DONE ✅)

The `GR3NB` GitHub organization has been created and the `rust-and-rainbow` repo has been transferred to it at:
`https://github.com/GR3NB/rust-and-rainbow`

## Step 2 — Upload the legal docs — 3 min

1. In the repo at github.com/GR3NB/rust-and-rainbow, click **Add file** → **Upload files**
2. Drag in the HTML files from:
   - `/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/legal/privacy.html`
   - `/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/legal/terms.html`
3. At the bottom: **Commit changes** → **Commit changes**

## Step 4 — Turn on GitHub Pages — 2 min

1. In the repo, click **Settings** (top right of the repo, not your account settings)
2. Left sidebar → **Pages**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**, folder: **/ (root)**
4. Click **Save**
5. Wait 1-2 minutes. GitHub will show a green box with your URL.

## Step 5 — Verify the URLs work

Open both in a fresh browser window:
- `https://gr3nb.github.io/rust-and-rainbow/privacy.html`
- `https://gr3nb.github.io/rust-and-rainbow/terms.html`

You should see the styled policy text. These are the canonical URLs to use everywhere.

## Step 6 — Update platform registrations

Now that the URLs have changed from `rcn723.github.io` to `gr3nb.github.io`, update these in:

| Platform | Where to update | Field |
|---|---|---|
| **TikTok** | developers.tiktok.com → App 7638050043181959175 | Privacy Policy URL + Terms URL |
| **Meta** | developers.facebook.com → your app | Privacy Policy URL |
| **Etsy** | developer.etsy.com → your app | Privacy Policy URL + Terms URL |

---

## Optional polish (skip for first submission, do later)

If you want them to look like normal web pages instead of raw markdown:
1. Rename `privacy.md` → `privacy.html` and wrap in basic HTML
2. Or enable a Jekyll theme: in Settings → Pages → Theme chooser → pick "Cayman" (free, clean)

Not required to get TikTok/Meta to accept the URLs. Only do this once you have spare time.

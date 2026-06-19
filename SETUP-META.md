# Meta (Facebook + Instagram) Setup — Field-by-Field Guide

**TL;DR:** The URL you sent me is the *user permissions* page in Business Manager. That part is essentially done — your business portfolio "RustandRainbow" exists, your Facebook Page and Instagram are connected, and you have full control. The actual API setup happens at a different site: `developers.facebook.com`. That's where we're heading next.

---

## What I found on the page you sent me

URL: `https://business.facebook.com/latest/settings/business_users?...`

This is **Meta Business Manager → Settings → Users → People**. State of your account:

| Item | Value | Notes |
|---|---|---|
| Business portfolio | RustandRainbow | Created, active |
| You (Rust Rain) | Full control | Good |
| Instagram @rustandrainbowco | Linked as "business user" | Treated as an unclaimed business user — that's normal |
| Facebook Page | "Rust and Rainbow" | Linked, partial access |
| Instagram account | rustandrainbowco | Linked, full control |
| Business ID | 970811995814374 | Save this — needed for some API calls |
| Facebook Page ID | 1135312136329438 | Save this for .env |
| **Instagram Business Account ID** | **1041492732390434** | **This is what goes in your .env as INSTAGRAM_BUSINESS_ACCOUNT_ID** |

**You don't need to do anything more on this page.** Don't change permissions or remove the unclaimed Instagram business user — that placeholder is normal.

---

## What you DO need to do at developers.facebook.com

This is the part that's actually missing. The Business Manager handles "who can access what assets." The Developer Portal handles "which apps can call the API on your assets." Different sites, different setup.

---

### Step 1 — Go to developers.facebook.com — 1 min

1. Open https://developers.facebook.com/apps in a fresh tab
2. Log in with the same Facebook account that owns the "Rust and Rainbow" Page (your Rust Rain account)
3. If first time: accept Developer terms

### Step 2 — Check if an app already exists — 1 min

You'll see "My Apps" with a list of any apps you've created. If you see one called "Rust and Rainbow" or similar, click it and skip to Step 4.

If the list is empty, continue to Step 3.

### Step 3 — Create the app — 5 min

1. Click **Create app**
2. **What do you want your app to do?** → Select **Other**
3. Click **Next**
4. **Select an app type** → Pick **Business** (this is required for Instagram Graph API access)
5. Click **Next**
6. **App name:** `Rust and Rainbow` (this is what's shown to users during OAuth)
7. **App contact email:** `rustandrainbow@gmail.com`
8. **Business portfolio:** select **RustandRainbow** from the dropdown (this connects the dev app to your existing Business Manager — important)
9. Click **Create app**
10. Confirm with your Facebook password

### Step 4 — Add Instagram Graph API product — 2 min

1. From the app dashboard, scroll to **Add products to your app**
2. Find **Instagram Graph API** → click **Set up**
3. (Note: As of late 2024 the old "Instagram Basic Display" was deprecated. Make sure you're picking "Instagram Graph API" or "Instagram" — both lead to the same place now.)

### Step 5 — Configure Instagram Business Login — 5 min

1. Left sidebar → **Instagram** → **Business Login**
2. **Set up redirect URI:** paste `https://YOUR_GITHUB_USERNAME.github.io/rustandrainbow/`
   - This satisfies Meta's requirement for a public redirect URL
   - You don't actually need a working OAuth callback for server-side scripts, but the field is required
3. **Allowed scopes** — check these:
   - `instagram_business_basic`
   - `instagram_business_content_publish` (this is the one that lets your script post)
   - `instagram_business_manage_insights` (for analytics)
   - `instagram_business_manage_comments` (optional — only if you want to read comments)
4. Click **Save changes**

### Step 6 — Connect your Instagram account — 2 min

1. Left sidebar → **Instagram** → **API Setup with Instagram Login**
2. Click **Add account**
3. Select your Instagram Business Account `@rustandrainbowco` from the list
4. Authorize all the scopes you enabled in Step 5

### Step 7 — Generate your long-lived access token — 5 min

1. Still in the Instagram setup section, click **Generate access token**
2. Walk through the OAuth flow — it'll send you to Instagram, you approve, and it returns a token
3. Copy the token — this is `META_ACCESS_TOKEN` in your `.env`
4. **Important:** This token expires in 60 days. Your `agent.py` should be updated to refresh it automatically. Set a calendar reminder for ~50 days from when you generate it as a backup.

### Step 8 — Fill in your .env — 2 min

Open `Rust & Rainbow/.env` and paste:

```
META_ACCESS_TOKEN=<paste the long-lived token from Step 7>
INSTAGRAM_BUSINESS_ACCOUNT_ID=1041492732390434
```

The Instagram Business Account ID is the one I pulled from your Business Manager URL above. Double-check it by going to the Instagram Account asset page in Business Manager — the ID in the URL bar should match.

### Step 9 — Submit app for review — only when ready

For Instagram Graph API publishing scopes (`instagram_business_content_publish`), Meta requires app review. The flow:

1. Left sidebar → **App Review** → **Permissions and Features**
2. Find each scope you need and click **Request advanced access**
3. For each, you'll need:
   - A screencast video showing how the app uses that permission
   - A written description of how the data is used
   - A link to your **privacy policy** (use the GitHub Pages URL)
4. Click **Submit for review**

Review typically takes 2-4 weeks for Meta. The same realism check applies as TikTok: don't submit until your `agent.py` actually works end-to-end and you can record a real screencast.

---

## Summary checklist

Before you can post to Instagram from the script, all of these must be true:

- [ ] Facebook Page "Rust and Rainbow" exists ✅ (already done)
- [ ] Instagram switched to Business or Creator account ✅ (already done)
- [ ] Instagram connected to Facebook Page ✅ (already done)
- [ ] Both linked to RustandRainbow Business Portfolio ✅ (already done)
- [ ] Developer app created at developers.facebook.com (Step 3)
- [ ] Instagram Graph API product added (Step 4)
- [ ] Redirect URI configured (Step 5)
- [ ] Token generated and pasted in .env (Steps 7-8)
- [ ] App submitted for review with publishing scopes (Step 9)
- [ ] Review approved (2-4 week wait)

---

## Pitfalls I see most often

1. **People skip linking the dev app to their Business Portfolio in Step 3.** Then later, they can't see their Instagram account in the API Setup screen because the app doesn't have access to the business that owns the IG account. If your account doesn't appear in Step 6, this is why — go to App Settings → Basic → Business and pick RustandRainbow.

2. **People use the test token from Graph API Explorer.** That token expires in 1 hour and isn't long-lived. Always go through the proper Business Login flow.

3. **People submit for review with no app icon, no detailed description, or a 5-second demo video.** Meta is stricter than TikTok about review quality. Your demo should be 60-120 seconds and walk through the full flow.

4. **People forget the 60-day token refresh.** Build the refresh into `agent.py` from the start, not later.

# TikTok Developer App — Field-by-Field Fill Guide

**App:** RustandRainbowClaude
**App ID:** 7638050043181959175
**URL:** https://developers.tiktok.com/app/7638050043181959175/pending

**Status when I checked:** Production tab, Draft, only the app name is filled.

---

## Why this order matters

TikTok's review takes 5-10 business days. Submitting an incomplete or sloppy app gets you a "rejection" that resets the clock. We're going to fill everything correctly, save as draft, then submit once your privacy/terms URLs go live and you have an icon and demo video.

**Tradeoff risk on Submit:** Rejected apps can get re-submitted, but each rejection adds 5-10 days to your timeline, and three rejections in a row can flag your developer account for manual review. Don't rush submit until everything is real.

---

## Section: Basic information

### App icon
- Upload a 1024x1024 PNG or JPG, under 5MB
- Suggested: a flat illustration of a vizsla head in your rust color (#B5451B) on cream (#F5F0E8)
- If you don't have one yet, use Ideogram (you already have an account) with this prompt:
  ```
  Minimalist flat illustration of a vizsla dog head in profile, warm rust orange color #B5451B, clean cream background #F5F0E8, simple line art, app icon style, centered, no text, square 1024x1024
  ```
- TikTok rejects icons that contain text, photos of real people, or logos that look like they belong to another brand

### App name
- Already filled: `RustandRainbowClaude`
- Tradeoff risk: This name will be shown to TikTok users when the account owner authorizes the app. "RustandRainbowClaude" is fine but not branded. Consider renaming to `Rust and Rainbow Studio` (more professional and matches your brand). To rename, click the pencil icon next to the name at the top.

### Category
- Select: **Business / Productivity**
- Why: Most accurate for an e-commerce automation tool. Reviewers expect this category for apps that post on behalf of a business account, and they tend to approve them faster than Lifestyle apps requesting the same scopes.

### Description (max 120 chars)
Paste exactly:
```
Print-on-demand brand for dog owners. We post short videos of our designs to @rustandrainbow on a 3x/week schedule.
```
(113 characters)

### Terms of Service URL
- Wait for GitHub Pages step. Once live, paste:
  `https://YOUR_GITHUB_USERNAME.github.io/rustandrainbow/terms.md`

### Privacy Policy URL
- Wait for GitHub Pages step. Once live, paste:
  `https://YOUR_GITHUB_USERNAME.github.io/rustandrainbow/privacy.md`

### Platforms
- Check: **Web** only
- Why: Your Python script runs server-side, which TikTok categorizes as a Web integration. You're not building an iOS or Android app. Checking extra platforms triggers extra review steps.

---

## Section: App review

### App review explanation (max 1000 chars)
Paste exactly:
```
Rust & Rainbow is a print-on-demand brand selling dog-themed apparel through Etsy. We use TikTok to share short marketing videos of our products on @rustandrainbow, posted on a 3x per week schedule from a server-side Python script.

Login Kit (user.info.basic, user.info.profile, user.info.stats): Used once during initial setup so the owner of @rustandrainbow can authorize the app to act on the account, and to read public follower and engagement counts to evaluate post performance.

Content Posting API (video.upload, video.list): A scheduled Python script uploads new product videos to the @rustandrainbow account as drafts. The account owner reviews each draft in the TikTok mobile app before publishing. video.list lets the script confirm successful upload and avoid duplicate uploads.

The integration acts only on a single owned account (@rustandrainbow). It is not multi-tenant and does not act on behalf of any other user.
```
(~970 chars)

### Demo video
- This is the hardest requirement. You must record a screen capture showing:
  1. The Python agent script running in your terminal
  2. An OAuth login flow where you authorize the app on @rustandrainbow
  3. The script uploading a video
  4. The video appearing in the TikTok drafts folder
  5. The script reading back stats / video list
- Format: mp4 or mov, under 50MB, 1-3 minutes
- Use QuickTime → File → New Screen Recording, or Loom (free)
- This must be a real recording — TikTok rejects mock-ups
- **Skip until your script actually works end-to-end.** Submitting a fake video can ban the developer account.

---

## Section: Products

Click "Add products" and select these two:

1. **Login Kit** — required, this is how the account owner authorizes the app
2. **Content Posting API** — required for video.upload and video.list

Do NOT add:
- Research API (you don't need it and it requires academic affiliation review)
- Commercial Content API (paid ads, not your use case)
- Display API (only needed if you're embedding TikTok content on a website)

### Inside Content Posting API: enable Direct Post?
- Leave "Direct Post" **disabled** for first submission
- Why: Direct Post = `video.publish` scope = posts go live immediately without owner review. TikTok rarely approves this for new apps with no existing user base. Apply for it in a follow-up revision after the first version is approved and you have proof of usage.
- You said you wanted automatic posting — the realistic path is: get drafts approved first (1-2 weeks), build 30-60 days of usage, then apply for Direct Post in a revision (another 1-2 weeks). Total: ~6-8 weeks before fully automatic posting is live. In the meantime, the agent uploads to drafts and you tap publish in the TikTok app.

---

## Section: Scopes

Click "Add scopes" and select:

| Scope | Why we need it |
|---|---|
| `user.info.basic` | Required minimum, identifies which TikTok account is connected |
| `user.info.profile` | Reads display name and bio so the agent can confirm it's the right account |
| `user.info.stats` | Reads public follower / like / video counts for analytics in `agent.py --mode monitor` |
| `video.upload` | Uploads videos to drafts |
| `video.list` | Reads list of videos already on the account, so the agent knows what's been posted |

Do NOT request:
- `video.publish` (yet — see Direct Post note above)
- `research.adlib.basic` (not relevant)

---

## Section: Save vs Submit

- **Save** button (top right): persists your draft, no review triggered. Click this every time you make changes.
- **Submit for review** button (top right): triggers TikTok's 5-10 day review. Only click when:
  - All fields above are filled
  - Privacy and Terms URLs are live and reachable
  - App icon is uploaded
  - Demo video is uploaded
  - You've tested OAuth flow end-to-end at least once

**Do not click Submit yet. We're not ready.**

---

## What's left after you fill this

In order:
1. Set up GitHub Pages (separate guide), get URLs
2. Come back, paste the two URLs into the form
3. Generate app icon via Ideogram
4. Build out the Python agent (`agent.py`) so it works end-to-end against the TikTok sandbox
5. Record the demo video showing the flow
6. Click Submit
7. Wait 5-10 business days

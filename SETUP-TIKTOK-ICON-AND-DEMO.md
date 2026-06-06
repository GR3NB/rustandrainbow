# TikTok Submission — App Icon + Demo Video Guide

**Why this exists:** TikTok blocks "Save" on the developer app form until you upload both an app icon and a demo video. Until they're uploaded, none of the form fields I filled (description, scopes, URLs, etc.) will persist if the browser tab refreshes.

**Order to do this in:**
1. Generate icon (~5 min, do today)
2. Build out `agent.py` so it works end-to-end against TikTok sandbox (this is the real engineering work — days, not hours)
3. Record demo video (~10 min, after agent works)
4. Come back to TikTok form, upload both, click Save, then Submit for review

---

## Part 1: App icon (do now)

### Requirements
- 1024 x 1024 pixels
- PNG, JPG, or JPEG
- Under 5 MB
- No text, no real people's faces, no other brand's logos
- Should look professional — TikTok rejects sloppy icons

### Generate via Ideogram (recommended)

1. Go to https://ideogram.ai (you already have an account)
2. Image → New
3. Aspect ratio: **1:1**
4. Quality: **High** (uses more credits but icon must look clean)
5. Paste this prompt:

```
Minimalist flat illustration of a vizsla dog head in profile, warm rust orange color #B5451B, clean cream background #F5F0E8, simple line art style, app icon design, centered composition, no text, no border, professional and modern aesthetic
```

6. Generate 4 variations
7. Pick the cleanest, most centered one. Avoid:
   - Anything with text (TikTok rejects)
   - Anything with humans
   - Anything overly busy or detailed
   - Anything that doesn't read clearly at small size (your icon will appear at 64x64 in lists)

8. Download the image
9. Verify size: should be at least 1024x1024. If it's smaller, regenerate with a higher resolution setting in Ideogram. Do NOT upscale a small image — TikTok will reject blurry icons.

### Alternative: Adobe Express

If Ideogram results don't land, you have access to the `adobe-design-from-template` skill in this Claude. Just say "design me a 1024x1024 app icon for Rust & Rainbow with a vizsla in rust orange on cream" and I'll produce one via Adobe Express.

### Where to upload

- Open https://developers.tiktok.com/app/7638050043181959175/pending
- Scroll to **Basic information** → **App icon**
- Click the empty `+` square
- Select your downloaded icon file
- TikTok will show a preview. If you like it, you're done with this step.

---

## Part 2: Demo video (do after agent.py works)

### What TikTok actually wants

A screen recording showing:
1. Your `agent.py` script running in your terminal
2. The OAuth flow where you (the @rustandrainbow account owner) authorize the app
3. The script successfully calling TikTok's API to upload a video
4. The uploaded video appearing in @rustandrainbow's TikTok drafts folder
5. The script reading back `video.list` (showing the script can see what it uploaded)

This **must** be a real recording of your real integration. TikTok rejects mock-ups, slideshows, or videos that are clearly just narration over a static screen.

### Specs
- Format: mp4 or mov
- Length: 60-120 seconds is the sweet spot (over 50 MB is rejected)
- Resolution: 1080p is fine, 720p is fine
- Audio: optional but helpful — narration explaining what you're doing reduces reviewer confusion
- Show the @rustandrainbow domain/handle clearly so reviewers can match it to the form

### Critical: Sandbox vs Production

> "If your app has not been approved before, you are required to use a sandbox environment on the Developer Portal to demonstrate the integration."

This means: **do your demo recording against the Sandbox tab in the TikTok developer portal, not Production.** Switch to the Sandbox tab (next to the Production tab at the top of the app form) before recording. Sandbox lets you test without affecting real user accounts.

### Recording flow (exact steps to capture)

1. Open QuickTime → File → New Screen Recording (or use Loom for free, https://loom.com)
2. Start recording
3. **Show your terminal** with `agent.py` ready to run
4. Run the OAuth setup command (e.g., `python agent.py --mode setup-tiktok`)
5. **Show the OAuth flow** — your browser opens, you log into @rustandrainbow on TikTok, authorize the app, get redirected
6. Back in terminal, **show the success message** — token saved
7. Run the upload command (e.g., `python agent.py --mode tiktok-test-upload`)
8. **Show the API call success** in terminal
9. **Open the TikTok mobile app** on your phone (or use the web at tiktok.com), log in as @rustandrainbow, navigate to drafts, **show the uploaded video sitting there**
10. Back in terminal, run something that calls `video.list` and **show it returns the just-uploaded video's ID**
11. Stop recording
12. Trim dead time, but don't cut so aggressively that TikTok reviewers can't follow the flow

### Where to upload

- Same TikTok app form, scroll to **App review** → **Required information for app submission**
- Click the **Upload** button under the demo video instructions
- Select your mp4/mov
- Wait for upload to finish (50 MB max)

---

## Part 3: Final save + submit (when both files are ready)

When you have icon + video ready:

1. Open https://developers.tiktok.com/app/7638050043181959175/pending in a fresh tab
2. **Check that all my pre-filled fields are still there.** If form is blank, the browser memory was wiped — tell me and I'll re-fill from `SETUP-TIKTOK.md`.
3. Upload icon (Part 1)
4. Upload demo video (Part 2)
5. Verify "This form has 0 errors" appears
6. Click **Save** (top right). Wait for confirmation toast.
7. **Don't click Submit yet.** Take a final look:
   - All URLs render in your browser correctly
   - Description and app review notes read well
   - Scopes match what you actually need (5 of them: user.info.basic, user.info.profile, user.info.stats, video.upload, video.list)
   - Direct Post is OFF (we're applying for drafts only first)
8. Tell me you've reviewed everything. I'll click Submit for review.
9. TikTok review takes 5-10 business days. Watch your developer email for the verdict.

---

## Common rejection reasons + how to avoid

| Reason | Fix |
|---|---|
| Icon contains text or another brand's logo | Use the Ideogram prompt above which excludes text |
| Demo video shows mockup, not real integration | Must be a real screen recording of working code |
| Privacy/Terms URLs return 404 | Already verified, but check before submit |
| App description sounds like spam or auto-generated | Mine reads cleanly. If you change it, keep it specific. |
| Direct Post requested with no usage history | We're applying for drafts only first. Direct Post application happens in a follow-up after first approval. |
| Demo video doesn't clearly show domain | Make sure your terminal title or a browser tab shows `rustandrainbow.github.io` somewhere visible |

---

## What I can do for you when you come back

- Re-fill any form fields that got wiped from browser memory
- Click Save once both files are uploaded
- Click Submit (only with your explicit confirmation, since this triggers review)
- Generate the icon via Adobe Express skill if Ideogram doesn't deliver

Don't refresh the TikTok tab in the meantime if you can avoid it. The verified URL prefix is saved server-side, but the unsaved form fields are not.

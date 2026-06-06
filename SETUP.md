# Rust & Rainbow — Setup Checklist

Complete these steps in order before running any agent scripts.
Each step links to exactly where you need to go.

---

## Step 1: Create Your Accounts (30 min)

### Etsy Shop
1. Go to etsy.com/sell
2. Click "Open your Etsy shop"
3. Shop name: **RustAndRainbow** (check availability — try RustAndRainbowCo if taken)
4. Set up billing (needed for $0.20 listing fees)
5. Skip adding listings for now — the agent handles that

### Printify Account
1. Go to printify.com → Sign up (free)
2. After signup: My Store → Connect → Select Etsy → Link your Etsy shop
3. Settings → API → Generate API key → copy it
4. Note your Shop ID from the URL when you're in your store dashboard

### Ideogram API
1. Go to ideogram.ai → create account
2. Settings → API → Create API key → copy it
3. Add credits: start with $5 (generates ~60-250 images depending on quality setting)

### Instagram Business Account
1. Create a new Instagram account: **@rustandrainbow** (try variations if taken)
2. Go to Settings → Account → Switch to Professional Account → Business
3. Connect to a Facebook Page (create one called "Rust & Rainbow" if you don't have one)
4. Go to developers.facebook.com → Create App → Business type
5. Add Instagram Graph API product
6. Generate a long-lived access token (valid 60 days — agent will remind you to refresh)
7. Note your Instagram Business Account ID

### TikTok Business Account
1. Create TikTok account: **@rustandrainbow**
2. Switch to Business Account: Profile → Settings → Manage Account → Switch to Business
3. Go to developers.tiktok.com → Manage Apps → Create App
4. Request Content Posting API access (may take 1-3 days for approval)
5. Note your Client Key and Client Secret

---

## Step 2: Configure Your Keys (5 min)

1. Open the `Rust & Rainbow` folder
2. Duplicate `.env.example` and rename the copy to `.env`
3. Fill in every value with your actual keys
4. Save and close — never share this file

---

## Step 3: Install Python Dependencies (5 min)

Open Terminal and run:

```bash
pip install requests python-dotenv moviepy pillow schedule
```

---

## Step 4: Run Your First Batch (15 min)

```bash
cd "/path/to/side business/Rust & Rainbow"
python agent.py --mode generate
```

This generates 10 designs for your approval. You'll see thumbnails and approve or skip each one. Approved designs get uploaded to Printify and published to Etsy automatically.

---

## Step 5: Activate Marketing Automation

Once at least 5 designs are live on Etsy:

```bash
python agent.py --mode market
```

This starts the posting schedule: Instagram 3x/week, TikTok 3x/week, fully automated.

---

## Step 6: Weekly Check-in

Run once a week (or let it run on a schedule):

```bash
python agent.py --mode monitor
```

Shows you sales data and flags underperformers for removal. Takes 2 minutes.

---

## Troubleshooting

**Ideogram returns errors:** Check your credit balance at ideogram.ai  
**Printify upload fails:** Verify your Shop ID is correct in .env  
**Instagram token expired:** Meta tokens last 60 days — regenerate at developers.facebook.com  
**TikTok API not approved yet:** Use manual posting via TikTok app until approval comes through  

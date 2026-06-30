# 🗺️ Find Leads on Google Maps

> **Automatically find business leads on Google Maps and export them to Google Sheets — with phone numbers, websites, ratings, addresses, and emails.**

Built for sales teams, freelancers, and marketers who want to generate B2B leads at scale without manual effort.

---

## ✨ Features

- 🔍 **Smart Multi-Pass Search** — Collects 40+ unique leads per query using location-bias technique (works without billing)
- 📞 **Full Business Details** — Name, phone, address, website, rating, review count, business hours
- 📧 **Email Extraction** — Automatically visits business websites to find contact emails
- 📊 **Google Sheets Export** — Results are written directly to your spreadsheet, organized by query
- 🔄 **Batch Mode** — Run 44 pre-defined queries automatically overnight
- 💻 **Interactive Mode** — Type any query and get results instantly
- 🛡️ **No Duplicates** — Deduplicates by `place_id` across all search passes

---

## 📸 How It Works

```
Your Query  →  Google Maps API  →  Multi-Pass Search  →  Email Extraction  →  Google Sheets
"gym in pune"      Places API        7 location offsets     Visit websites      Auto-appended
                   (free tier)       = 40-60 unique leads   find contact@...    to your sheet
```

---

## 🗂️ Project Structure

```
FindingBots/
│
├── main.py                  # Interactive / single-query runner
├── batch_run.py             # Batch runner for 44 pre-built queries
├── requirements.txt         # Python dependencies
├── .env.example             # Template for your credentials
├── .env                     # Your credentials (DO NOT commit)
├── service_account.json     # Google service account key (DO NOT commit)
│
└── bot/
    ├── google_maps.py       # Google Maps Places API — multi-pass search
    ├── data_processor.py    # Cleans and normalises raw API data
    ├── email_extractor.py   # Scrapes websites for contact emails
    └── sheets_writer.py     # Writes rows to Google Sheets via gspread
```

---

## ⚙️ Full Setup Guide

> Estimated time: **10–15 minutes**. One-time setup, runs forever after.

---

### Step 1 — Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name it `FindingBots` (or anything you like)
4. Click **Create** and wait for it to be ready

---

### Step 2 — Enable Required APIs

Inside your new project:

1. Go to **APIs & Services** → **Library**
2. Search and **Enable** each of these:

| API | Purpose |
|-----|---------|
| ✅ **Places API** (or Places API New) | Search businesses on Google Maps |
| ✅ **Google Sheets API** | Write data to your spreadsheet |
| ✅ **Google Drive API** | Required by gspread for sheet access |

> 💡 Search each one by name, click on it, then click the blue **Enable** button.

---

### Step 3 — Create a Google Maps API Key

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **API key**
3. Copy the key (looks like `AIzaSyXXXXXXXXXXXXXXXXXXXX`)
4. *(Recommended)* Click the key → **Restrict key** → Select **Places API** → Save

> ⚠️ Keep this key private. Never commit it to GitHub.

---

### Step 4 — Create a Service Account (for Google Sheets)

The bot needs a **Service Account** to write to your Google Sheet automatically.

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **+ CREATE SERVICE ACCOUNT**
3. Fill in:
   - **Name**: `findingbots-sheets`
   - **Description**: `FindingBots Sheets Writer` *(optional)*
4. Click **Create and Continue** → **Done**
5. Click on your new service account in the list
6. Go to the **Keys** tab → **Add Key** → **Create new key** → **JSON**
7. A `.json` file will download automatically
8. **Rename it** to `service_account.json`
9. **Move it** into your `FindingBots/` project folder

> ✅ The file stays on your computer only — it's in `.gitignore` and will never be pushed to GitHub.

---

### Step 5 — Share Your Google Sheet with the Service Account

1. Open (or create) the Google Sheet where results will be saved
2. Open your `service_account.json` file and find the `"client_email"` field:
   ```
   "client_email": "findingbots-sheets@your-project.iam.gserviceaccount.com"
   ```
3. In your Google Sheet, click **Share** (top right)
4. Paste that email address
5. Set role to **Editor**
6. Click **Send**

> 📋 Copy the **Sheet ID** from the URL — you'll need it in the next step:
> ```
> https://docs.google.com/spreadsheets/d/  ← SHEET_ID_IS_HERE →  /edit
> ```

---

### Step 6 — Configure Your `.env` File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your values:
   ```env
   # Your Google Maps API Key (from Step 3)
   GOOGLE_MAPS_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXX

   # Your Google Sheet ID (from the sheet URL)
   GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms

   # Path to your service account file (from Step 4)
   GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

   # Max results per query (20–60 recommended)
   MAX_RESULTS=45
   ```

---

### Step 7 — Install Python Dependencies

Make sure you have Python 3.8+ installed, then run:

```bash
cd FindingBots
pip install -r requirements.txt
```

**Dependencies installed:**

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | ≥2.31 | HTTP calls to Google Maps API |
| `gspread` | ≥6.0 | Google Sheets read/write |
| `google-auth` | ≥2.28 | Service account authentication |
| `python-dotenv` | ≥1.0 | Load `.env` credentials |
| `rich` | ≥13.7 | Beautiful terminal output |
| `beautifulsoup4` | ≥4.12 | Website email scraping |

---

### Step 8 — Run the Bot 🚀

#### Interactive Mode *(recommended for exploring)*

```bash
python main.py
```

Type any search query when prompted:

```
🔍 Search query: gym in Pune
🔍 Search query: hospital in Chakan
🔍 Search query: software companies in Hinjewadi
```

Type `quit` or `exit` to stop.

---

#### Single Query Mode

```bash
python main.py "hospital in chakan"
```

#### With Options

```bash
# Limit number of results
python main.py "hotel in pune" --max-results 20

# Skip email extraction (2x faster)
python main.py "industries in pune" --no-email

# Combine flags
python main.py "gym in pune" --max-results 30 --no-email
```

---

#### Batch Mode — 44 Queries Automatically

Run all 44 pre-built queries for Pune businesses in one go:

```bash
python batch_run.py
```

```bash
# Skip emails for speed
python batch_run.py --no-email

# Limit results per query
python batch_run.py --max-results 30

# Resume from a specific query number
python batch_run.py --start 73
```

Pre-built query categories include:
- 🏋️ Gyms & Fitness, 🏥 Hospitals & Clinics
- 🏨 Hotels & Resorts, 🚗 Auto Dealerships
- 🐾 Pet Shops & Vets, ☕ Cafes & Restaurants
- 💻 IT & Software Companies, 🏗️ Construction
- and 36 more...

---

## 📊 Output — What Gets Written to Your Sheet

Each query creates a **new tab** in your Google Sheet named after the query:

| Column | Example |
|--------|---------|
| Sr No | 1 |
| Business Name | Gold's Gym Chakan |
| Category | Health & Fitness |
| Phone | +91 98765 43210 |
| Email | contact@goldsgym.in |
| Website | goldsgym.in |
| Address | Chakan, Pune 410501 |
| Rating | 4.5 |
| Reviews | 312 |
| Business Status | OPERATIONAL |
| Google Maps URL | maps.google.com/... |
| Query | gym in chakan |

---

## 🔧 Troubleshooting

### ❌ `API key not valid`
- Make sure you copied the **full** API key with no extra spaces
- Go to Cloud Console → Credentials and verify the key is active
- Ensure **Places API** is enabled (Step 2)

### ❌ `SpreadsheetNotFound`
- Double-check the **Sheet ID** in your `.env` file
- Make sure you shared the sheet with the **service account email** (Step 5)
- The service account email must have **Editor** access

### ❌ `Service account file not found`
- Ensure `service_account.json` is inside the `FindingBots/` folder
- Check `GOOGLE_SERVICE_ACCOUNT_FILE` in your `.env` matches the filename exactly

### ❌ `REQUEST_DENIED` or `This API project is not authorized`
- Go to Google Cloud → **APIs & Services** → **Library**
- Re-enable **Places API**, **Sheets API**, and **Drive API**

### ⚠️ Only getting 20 results
- This is expected for very niche or small areas — there may only be 20 businesses
- For broader queries (e.g. "restaurants in Pune"), the multi-pass search will return 40–60+
- Enabling billing on Google Cloud unlocks native pagination (up to 60 per query via tokens)

---

## 💰 Cost Estimate

Google Maps gives you **$200 free credit per month**. This project stays well within that:

| Operation | Cost per Call | Typical Monthly Usage | Cost |
|-----------|-------------|----------------------|------|
| Text Search (Places API) | $0.032 / call | ~300 searches | ~$9.60 |
| Place Details | $0.017 / call | ~1,500 lookups | ~$25.50 |
| **Total** | | | **~$35 / month** |

> ✅ Well within the **$200 free tier**. You'll likely pay $0.

---

## 🔒 Security Notes

- `.env` and `service_account.json` are in `.gitignore` — they will **never** be pushed to GitHub
- Never share your API key or service account JSON publicly
- If you accidentally expose them, rotate immediately:
  - **API Key**: Cloud Console → Credentials → Regenerate
  - **Service Account**: IAM & Admin → Service Accounts → Keys → Delete old key → Add new key

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.

See [LICENSE](LICENSE) for full text.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

<div align="center">
  Made with ❤️ for lead generation automation
  <br/>
  <a href="https://github.com/Ashutosh8454/Find-leads-on-Google-Map">⭐ Star this repo if it helped you!</a>
</div>

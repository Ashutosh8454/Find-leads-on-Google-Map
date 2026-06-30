# 🗺️ Google Maps Business Finder Bot — Setup Guide

Follow these steps to set up the bot. It should take about 10 minutes.

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name it something like `FindingBots`
4. Click **Create**

---

## Step 2: Enable Required APIs

In your Google Cloud project:

1. Go to **APIs & Services** → **Library**
2. Search for and **Enable** these 3 APIs:
   - ✅ **Places API (New)** — for searching businesses on Google Maps
   - ✅ **Google Sheets API** — for writing data to your spreadsheet
   - ✅ **Google Drive API** — required by gspread for sheet access

---

## Step 3: Create a Google Maps API Key

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **API key**
3. Copy the API key (looks like `AIzaSy...`)
4. ⚠️ **Recommended**: Click on the key to edit it, and restrict it to **Places API (New)** only

---

## Step 4: Create a Service Account (for Google Sheets)

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **+ CREATE SERVICE ACCOUNT**
3. Name: `findingbots-sheets` (or any name)
4. Click **Create and Continue** → **Done**
5. Click on the newly created service account
6. Go to the **Keys** tab
7. Click **Add Key** → **Create new key** → **JSON**
8. The JSON file will download — **rename it to `service_account.json`**
9. Move it to the `FindingBots/` folder

---

## Step 5: Share Your Google Sheet

1. Open your Google Sheet: [findclientbotsystem](https://docs.google.com/spreadsheets/d/1jvSItZiV3ye0zF6l1oMm1z05N1tU18QsgAjyptYk9NY/edit)
2. Open the downloaded `service_account.json` file
3. Find the `"client_email"` field — it looks like: `findingbots-sheets@your-project.iam.gserviceaccount.com`
4. Click **Share** on the Google Sheet
5. Paste the `client_email` address
6. Set permission to **Editor**
7. Click **Send**

---

## Step 6: Configure Environment Variables

1. Copy the example env file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```
   GOOGLE_MAPS_API_KEY=AIzaSy...your_actual_key...
   GOOGLE_SHEET_ID=1jvSItZiV3ye0zF6l1oMm1z05N1tU18QsgAjyptYk9NY
   GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
   MAX_RESULTS=60
   ```

---

## Step 7: Install Dependencies

```bash
cd FindingBots
pip install -r requirements.txt
```

---

## Step 8: Run the Bot! 🚀

### Interactive Mode (recommended):
```bash
python main.py
```
Then type queries like:
- `hospital in chakan`
- `industries in pune`
- `hotel in chakan`

### Single Query Mode:
```bash
python main.py "hospital in chakan"
```

### Options:
```bash
python main.py "hospital in chakan" --max-results 20    # Limit results
python main.py "hotel in pune" --no-email                # Skip email extraction (faster)
```

---

## Troubleshooting

### ❌ "API key not valid"
- Make sure you copied the full API key
- Check that **Places API (New)** is enabled in your Google Cloud project

### ❌ "SpreadsheetNotFound"
- Make sure you shared the Google Sheet with the service account email (Step 5)
- Check that the Sheet ID in `.env` is correct

### ❌ "Service account file not found"
- Make sure `service_account.json` is in the `FindingBots/` folder
- Check the `GOOGLE_SERVICE_ACCOUNT_FILE` path in `.env`

### ❌ "REQUEST_DENIED" or "This API project is not authorized"
- Enable the **Places API (New)** in Google Cloud Console (Step 2)
- Make sure billing is enabled on your Google Cloud project (free $200/month credit)

---

## Cost

Google gives you **$200/month free credit** for Maps APIs. Typical usage:

| Action | Cost |
|--------|------|
| 10 queries × 20 results = 200 API calls | ~$5-7 (well within free tier) |
| Google Sheets API | Free (unlimited) |

You'll only pay if you exceed the $200/month free credit.

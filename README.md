# Trello Data Export and Backup Tool

**Export Trello boards to JSON/CSV with attachments** - A comprehensive Python script for backing up and migrating Trello data. Perfect for data archival, analysis, or moving away from Trello.

**Keywords**: Trello export, Trello backup, Trello data migration, Trello archival, export Trello boards, download Trello attachments, Trello to CSV, Trello API export

A complete solution that exports your Trello boards to local JSON and CSV files, including downloading all card attachments. Uses secure OAuth1 authentication to access your Trello data and creates organized, portable exports.

## What This Tool Does

✅ **Complete Trello Export**: Export all your Trello boards with full data
✅ **Attachment Download**: Download all images and files from cards
✅ **Multiple Formats**: Get data as JSON (complete) and CSV (spreadsheet-ready)
✅ **Batch Processing**: Export all boards at once or individual boards
✅ **Data Migration Ready**: Perfect for moving data out of Trello
✅ **Backup Solution**: Create complete local backups of your Trello workspace

## Use Cases

- **Data Backup**: Create complete backups of your Trello workspace
- **Data Migration**: Export data before switching to another project management tool
- **Analysis**: Import CSV data into Excel, Google Sheets, or databases for reporting
- **Archival**: Long-term storage of completed project data
- **Compliance**: Meet data retention requirements by maintaining local copies

## Performance

- Tested once with a board containing 920 cards, 57 images, and 119 url attachments
- Downloaded all cards in about 2 seconds
- Downloaded all cards and attachments (including urls and images) in about 5 minutes

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Trello API Credentials

1. Go to [Trello's Developer Portal](https://trello.com/app-key)
2. Log in with your Trello account
3. You'll see your **API Key** - copy this value
4. Click "Generate a new secret" to get your **API Secret** - copy this value

### 3. Create Environment File

Create a `.env` file in the project directory with the following variables:

```env
TRELLO_KEY=your_api_key_here
TRELLO_SECRET=your_api_secret_here
TRELLO_RETURN_URL=oob
```

**Required Variables:**
- `TRELLO_KEY` - Your Trello API consumer key (from step 2)
- `TRELLO_SECRET` - Your Trello API consumer secret (from step 2)
- `TRELLO_RETURN_URL` - OAuth callback URL (use "oob" for out-of-band auth)

**Optional Variables (automatically set after first run):**
- `TRELLO_TOKEN` - Access token (obtained during OAuth flow)
- `TRELLO_TOKEN_SECRET` - Token secret (obtained during OAuth flow)

## Usage

Run the script:

```bash
python trello_backup.py
```

### First Run (Authentication)

On your first run, the script will guide you through OAuth authentication:

1. The script will display a Trello authorization URL
2. Visit the URL in your browser and authorize the application
3. Trello will show you a PIN code
4. Enter the PIN code in the terminal
5. The script will save your access tokens for future use

### Output

The script creates a `trello_exports/` directory containing:

- **Individual board directories** (named by sanitized board name)
- **JSON files** with complete board data: `board_{name}_{id}.json`
- **Attachments folder** with card-specific subfolders: `attachments/{card_id}_{attachment_id}/`
- **Combined CSV file** with all boards data: `trello_export.csv`

## Configuration Options

### Export Settings

The script includes configuration options at the top of `trello_backup.py`:

```python
DEBUG = False
DEBUG_BOARD_ID = "5f67b24e3bf4a71838a837cf"
DOWNLOAD_ATTACHMENTS = True
```

**Export Controls:**
- **`DEBUG = False`** (default): Exports all boards and all cards
- **`DEBUG = True`**: Only processes cards from the specified board ID in `DEBUG_BOARD_ID`
- **`DOWNLOAD_ATTACHMENTS = True`** (default): Downloads all attachments
- **`DOWNLOAD_ATTACHMENTS = False`**: Skips attachment downloads (faster, metadata only)

**For Testing or Selective Export:**
1. Set `DEBUG = True`
2. Replace `DEBUG_BOARD_ID` with your target board's ID
3. Run the script to export only that specific board

**For Faster Exports (No Files):**
1. Set `DOWNLOAD_ATTACHMENTS = False`
2. This will still download board name, list name, title of item, and description of item, but it will not download images or urls stored as attachments. (Urls in the description or title will be downloaded properly.)

## Troubleshooting

- **Authentication errors**: Verify your API key and secret are correct
- **Rate limiting**: The script automatically handles Trello's rate limits
- **Missing attachments**: Only Trello-hosted attachments are downloaded
- **Debug mode**: Use `DEBUG = True` to limit exports to a specific board for testing

## Acknowledgements
This script and documentation was written with the help of ChatGPT and Anthropic Claude Code.

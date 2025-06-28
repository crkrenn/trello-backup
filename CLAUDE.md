# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Trello backup tool that exports Trello boards to JSON and CSV formats with attachment downloads. The script uses OAuth1 authentication to access the Trello API and creates organized exports with local file storage.

## Setup and Configuration

### Environment Variables Required
Create a `.env` file with these variables:
- `TRELLO_KEY` - Trello API consumer key  
- `TRELLO_SECRET` - Trello API consumer secret
- `TRELLO_RETURN_URL` - OAuth callback URL (defaults to "oob")
- `TRELLO_TOKEN` - Access token (obtained after first run)
- `TRELLO_TOKEN_SECRET` - Token secret (obtained after first run)

### Dependencies
Install dependencies with:
```bash
pip install -r requirements.txt
```

## Running the Tool

Execute the main script:
```bash
python trello_backup.py
```

On first run, the script will guide you through OAuth1 authentication to obtain access tokens.

## Code Architecture

### Core Components

- **OAuth1 Flow** (`trello_backup.py:38-78`): Handles initial authentication and token acquisition
- **API Client** (`trello_backup.py:81-100`): OAuth1 session management and rate-limited API requests
- **Board Export** (`trello_backup.py:115-201`): Exports individual boards with full data and attachments
- **CSV Export** (`trello_backup.py:204-218`): Consolidates all board data into a single CSV file

### Export Structure

The tool creates a `trello_exports/` directory containing:
- Individual board directories (named by sanitized board name)
- JSON files with complete board data: `board_{slug}_{board_id}.json`
- `attachments/` subdirectory with card-specific attachment folders
- Combined `trello_export.csv` with all boards data

### Key Features

- **Rate Limiting**: Automatic retry with backoff on 429 responses
- **Attachment Filtering**: Only downloads Trello-hosted attachments from card URLs
- **Debug Mode**: Can filter to specific lists using `DEBUG` flag and hardcoded list ID
- **File Safety**: Sanitizes filenames and skips existing downloads

### Important Notes

- The script contains commented-out legacy code that should be cleaned up
- Debug mode on line 21 may limit exports to specific lists
- Attachment download logic filters for Trello card URLs specifically
- All exports are organized under the `trello_exports/` directory
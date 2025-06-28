#!/usr/bin/env python3
# export_trello_oauth.py
# Requires a .env file with the following variables:
# TRELLO_KEY           — your Trello API consumer key
# TRELLO_SECRET        — your Trello API consumer secret
# TRELLO_RETURN_URL    — your OAuth callback URL (must match allowed origins in Trello app settings)
# (Optional, after first run)
# TRELLO_TOKEN         — obtained access token
# TRELLO_TOKEN_SECRET  — obtained token secret

import os
import sys
import time
import json
import csv
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

DEBUG = True
DEBUG_BOARD_ID = "5f67b24e3bf4a71838a837cf"

# ─── 1) LOAD ENV VARIABLES ─────────────────────────────────────────────────────
load_dotenv()
CONSUMER_KEY    = os.getenv("TRELLO_KEY")
CONSUMER_SECRET = os.getenv("TRELLO_SECRET")
CALLBACK_URI    = os.getenv("TRELLO_RETURN_URL", "oob")
API_BASE_URL    = os.getenv("TRELLO_API_URL", "https://api.trello.com/1")

if not CONSUMER_KEY or not CONSUMER_SECRET:
    print("Error: TRELLO_KEY and TRELLO_SECRET must be set in .env", file=sys.stderr)
    sys.exit(1)

# ─── 2) OAUTH1 FLOW IF NEEDED ────────────────────────────────────────────────────
ACCESS_TOKEN = os.getenv("TRELLO_TOKEN")
TOKEN_SECRET = os.getenv("TRELLO_TOKEN_SECRET")

if not ACCESS_TOKEN or not TOKEN_SECRET:
    print("ℹ️  Starting Trello OAuth1 flow to obtain access token/secret…\n")
    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        callback_uri=CALLBACK_URI
    )
    req = oauth.fetch_request_token("https://trello.com/1/OAuthGetRequestToken")
    resource_owner_key    = req["oauth_token"]
    resource_owner_secret = req["oauth_token_secret"]

    auth_url = oauth.authorization_url(
        "https://trello.com/1/OAuthAuthorizeToken",
        name="Trello Exporter Script",
        scope="read",
        expiration="never"
    )
    print("1) Go to:\n   ▶️", auth_url, "\n")
    if CALLBACK_URI.lower() != "oob":
        print(f"After approving, you'll be redirected to: {CALLBACK_URI}\n")
        verifier = input("2) Paste the 'oauth_verifier' parameter from the callback URL here: ").strip()
    else:
        verifier = input("2) Enter the Trello PIN here: ").strip()

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier
    )
    tokens = oauth.fetch_access_token("https://trello.com/1/OAuthGetAccessToken")
    ACCESS_TOKEN = tokens["oauth_token"]
    TOKEN_SECRET = tokens["oauth_token_secret"]

    print("\n✅ Got Access Token:", ACCESS_TOKEN)
    print("✅ Got Token Secret:", TOKEN_SECRET)
    print("\n👉 Save these in your `.env` as:\n")
    print("   TRELLO_TOKEN=", ACCESS_TOKEN)
    print("   TRELLO_TOKEN_SECRET=", TOKEN_SECRET)
    print("\n—then re-run this script to skip authorization next time.\n")

# ─── 3) PREPARE OAUTH1 SESSION ──────────────────────────────────────────────────
def oauth1_session():
    return OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=TOKEN_SECRET,
        callback_uri=CALLBACK_URI
    )

# ─── 4) TRELLLO HELPER FUNCTIONS ────────────────────────────────────────────────
def trello_get(endpoint: str, **params):
    """GET request with OAuth1 + rate-limit backoff."""
    url = f"{API_BASE_URL}{endpoint}"
    sess = oauth1_session()
    resp = sess.get(url, params=params)
    if resp.status_code == 429:
        time.sleep(int(resp.headers.get("Retry-After", 3)))
        return trello_get(endpoint, **params)
    resp.raise_for_status()
    return resp.json()


def download_file(url: str, dest: Path):
    """Stream-download a URL to local path (skip if exists)."""
    if dest.exists():
        return
    sess = oauth1_session()
    resp = sess.get(url, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)

# ─── 5) EXPORT LOGIC ────────────────────────────────────────────────────────────
def export_board(board):
    board_id   = board["id"]
    board_name = board["name"]
    print(f"\n📋 Exporting board: {board_name} ({board_id})")
    slug      = "".join(c if c.isalnum() else "_" for c in board_name)
    board_dir = Path(slug)
    data = trello_get(f"/boards/{board_id}",
        lists="all",
        cards="all",
        checklists="all",
        card_attachments="true",
        attachment_fields="name,url",
        fields="name,desc,closed,dateLastActivity"
    )

    # For each card, download attachments matching Trello card URLs
    for card in data.get('cards', []):
        if DEBUG and card.get('idList') != DEBUG_BOARD_ID:
            continue
        atts = card.get('attachments', []) or trello_get(f"/cards/{card['id']}/attachments")

        # filter relevant URLs and keep attachment objects
        def is_trello_card_image(att):
            url = att.get('url', '')
            return bool(url) and 'trello.com' in url and '/cards/' in url

        atts_with_images = [att for att in atts if is_trello_card_image(att)]
        atts_with_urls   = [att for att in atts if att.get('url') and not is_trello_card_image(att)]

        if atts_with_urls:
            urls = [att.get('url') for att in atts_with_urls]
            print("urls: ", urls)
            card['local_attachments'] = urls

        if not atts_with_images:
            continue
        # only create attachments directory if needed
        attachments_dir = board_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        card_id = card['id']
        for att in atts_with_images:
            url = att.get('url')
            # extract attachment ID from URL
            path_parts = urlparse(url).path.split('/')
            try:
                att_idx = path_parts.index('attachments') + 1
                attachment_id = path_parts[att_idx]
            except (ValueError, IndexError):
                attachment_id = 'unknown'

            # create directory with card_id and attachment_id
            att_dir = attachments_dir / f"{card_id}_{attachment_id}"
            att_dir.mkdir(exist_ok=True)
            # extract filename
            filename = att.get('name') or path_parts[-1]
            safe_name = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in filename)
            dest = att_dir / safe_name
            print(f"↓ Downloading {safe_name} to {card_id}_{attachment_id}/")
            try:
                download_file(url, dest)
                card.setdefault('local_attachments', []).append(f"{dest}")
            except Exception as e:
                print(f"⚠️ Failed {safe_name}: {e}")(
                    f"/boards/{board_id}",
                    lists="all",
                    cards="all",
                    checklists="all",
                    card_attachments="true",
                    attachment_fields="name,url",
                    fields="name,desc,closed,dateLastActivity"
                )
                dest = "failed"

    # write JSON
    out_json = board_dir / f"board_{slug}_{board_id}.json"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"✅ Wrote JSON: {out_json}")

    return data, board_name


def export_csv(all_boards):
    """Export combined CSV of all boards data."""
    csv_file = Path("trello_export.csv")
    with open(csv_file, "w", newline='', encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        writer.writerow(["board", "list", "item", "description", "attachments"])
        for data, board_name in all_boards:
            lists = {lst['id']: lst['name'] for lst in data.get('lists', [])}
            for card in data.get('cards', []):
                list_name = lists.get(card['idList'], '')
                item = card.get('name', '')
                desc = card.get('desc', '').replace('\n', ' ')
                atts = ';'.join(card.get('local_attachments', []))
                writer.writerow([board_name, list_name, item, desc, atts])
    print(f"✅ Wrote CSV: {csv_file}")


def main():
    root = Path("trello_exports")
    root.mkdir(exist_ok=True)
    os.chdir(root)

    boards = trello_get("/members/me/boards", fields="name,closed,dateLastActivity")
    active = [b for b in boards if not b.get("closed")]
    print(f"Found {len(active)} active boards.")

    all_data = []
    for b in active:
        data, name = export_board(b)
        all_data.append((data, name))

    export_csv(all_data)
    print("\n🎉 All done.")

if __name__ == "__main__":
    main()

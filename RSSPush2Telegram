import feedparser
import requests
import os
import time
import json

TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')
DB_FILE = "sent_links.txt"
CONFIG_FILE = "feeds.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f).get("feeds", [])

def load_sent_links():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_sent_link(link):
    with open(DB_FILE, "a") as f:
        f.write(link + "\n")

def send_tg_message(title, link):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    text = f"<b>{title}</b>\n\n{link}"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(api_url, data=payload, timeout=10)
        if response.status_code == 429:
            retry_after = response.json().get('parameters', {}).get('retry_after', 5)
            time.sleep(retry_after)
            return requests.post(api_url, data=payload).status_code
        return response.status_code
    except Exception as e:
        print(f"Post error: {e}")
        return None

def main():
    feeds = load_config()
    sent_links = load_sent_links()
    
    for url in feeds:
        print(f"Scanning: {url}")
        try:
            feed = feedparser.parse(url)
            for entry in reversed(feed.entries):
                if entry.link not in sent_links:
                    status = send_tg_message(entry.title, entry.link)
                    if status == 200:
                        save_sent_link(entry.link)
                        sent_links.add(entry.link)
                        print(f"Sent: {entry.title}")
                    time.sleep(1.5) 
        except Exception as e:
            print(f"Skip {url} due to error: {e}")

if __name__ == "__main__":
    main()

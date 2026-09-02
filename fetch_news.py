#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import time
from deep_translator import GoogleTranslator

RSS_FEEDS = [
    "https://www.konami.com/games/efootball/feed/",
    "https://www.reddit.com/r/eFootball/.rss",
    "https://feeds.feedburner.com/ign/news"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def translate_text(text):
    if not text:
        return text
    try:
        translated = GoogleTranslator(source='auto', target='ar').translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"Translation failed for '{text[:20]}...': {e}")
        return text

def parse_rss_feed(feed_url):
    articles = []
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else datetime.now().isoformat()
                
                if title and link:
                    translated_title = translate_text(title)
                    articles.append({
                        "title": translated_title,
                        "link": link,
                        "pubDate": pubDate
                    })
    except Exception as e:
        print(f"Error fetching {feed_url}: {e}")
    return articles

def main():
    print("Fetching and translating eFootball news...")
    all_articles = []
    
    for feed in RSS_FEEDS:
        articles = parse_rss_feed(feed)
        all_articles.extend(articles)
        time.sleep(1)

    unique_articles = {v['link']: v for v in all_articles}.values()
    final_list = list(unique_articles)

    if final_list:
        with open('efootball_news.json', 'w', encoding='utf-8') as f:
            json.dump(final_list, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(final_list)} articles!")

if __name__ == "__main__":
    main()
    

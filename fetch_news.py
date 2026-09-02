#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import time
import re
from deep_translator import GoogleTranslator

# مصادر الأخبار والتسريبات المباشرة
RSS_FEEDS = [
    "https://www.konami.com/games/efootball/feed/",
    "https://www.reddit.com/r/eFootball/.rss",
    "https://www.reddit.com/r/pesmobile/.rss"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# كلمات مفتاحية مرنة تشمل مصطلحات اللعبة الشائعة
KEYWORDS = ['efootball', 'pes', 'konami', 'potw', 'epic', 'booster', 'mobile', 'update', 'patch', 'coins', 'card', 'messi', 'pack', 'leak', 'game', 'season', 'match', 'event']

def translate_text(text):
    if not text or len(text.strip()) == 0:
        return ""
    try:
        clean_text = re.sub('<[^<]+?>', '', text).strip()
        if 'Error 500' in clean_text or 'Server Error' in clean_text:
            return ""
        truncated = clean_text[:800]
        translated = GoogleTranslator(source='auto', target='ar').translate(truncated)
        return translated if translated else clean_text
    except Exception as e:
        print(f"Translation error: {e}")
        return re.sub('<[^<]+?>', '', text).strip()

def extract_image_url(item, description_text):
    for elem in item.iter():
        if 'content' in elem.tag or 'thumbnail' in elem.tag or elem.tag == 'enclosure':
            url = elem.attrib.get('url')
            if url and any(url.endswith(ext) for ext in ['.jpg', '.png', '.jpeg', '.webp']):
                return url
    if description_text:
        img_match = re.search(r'<img [^>]*src=["\']([^"\']+)["\']', description_text)
        if img_match:
            return img_match.group(1)
            
    return "https://www.konami.com/games/efootball/common/images/share.png"

def parse_rss_feed(feed_url):
    articles = []
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item')[:10]:
                title_en = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else datetime.now().isoformat()
                
                desc_elem = item.find('description')
                description_raw = desc_elem.text if desc_elem is not None else ''
                details_en = re.sub('<[^<]+?>', '', description_raw).strip()
                
                # استبعاد أخطاء السيرفرات فقط
                if 'Error 500' in title_en or 'Server Error' in title_en:
                    continue

                image_url = extract_image_url(item, description_raw)

                if title_en and link:
                    title_ar = translate_text(title_en)
                    details_ar = translate_text(details_en) if details_en else title_ar

                    articles.append({
                        "title": title_ar,
                        "title_en": title_en,
                        "details": details_ar,
                        "details_en": details_en if details_en else title_en,
                        "image": image_url,
                        "link": link,
                        "pubDate": pubDate
                    })
    except Exception as e:
        print(f"Error fetching {feed_url}: {e}")
    return articles

def main():
    print("Fetching eFootball news...")
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
        print(f"Saved {len(final_list)} articles successfully!")

if __name__ == "__main__":
    main()
    

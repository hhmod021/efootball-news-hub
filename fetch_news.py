#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import time
import re
import html
from deep_translator import GoogleTranslator

KONAMI_INFO_URL = "https://www.konami.com/games/efootball/en/page/2025/info_detail"
RSS_FEEDS = [
    "https://www.reddit.com/r/eFootball/search.rss?q=flair_name%3A%20%22Official%22&restrict_sr=1&sort=new",
    "https://www.reddit.com/r/pesmobile/search.rss?q=flair_name%3A%20%22Update%22&restrict_sr=1&sort=new"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    text = re.sub(r'<[^<]+?>', '', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'u/\S+', '', text)
    return text.strip()

def translate_to_arabic(text):
    if not text:
        return ""
    try:
        clean = clean_text(text)[:600]
        if "Error 500" in clean or "Server Error" in clean:
            return ""
        translated = GoogleTranslator(source='auto', target='ar').translate(clean)
        return translated if translated else clean
    except Exception as e:
        return clean_text(text)

def categorize_article(title_en):
    """تصنيف الخبر: صيانة وإصلاحات أم تحديثات وإضافات"""
    title_lower = title_en.lower()
    maintenance_keywords = ['maintenance', 'issue', 'fix', 'notice', 'server', 'error', 'bug', 'compensation']
    if any(k in title_lower for k in maintenance_keywords):
        return "maintenance"
    return "updates"

def parse_rss_feed(feed_url):
    articles = []
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')

            for item in items[:10]:
                title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                title_en = clean_text(title_elem.text) if title_elem is not None and title_elem.text else ''

                if not title_en or 'Error 500' in title_en or 'Server Error' in title_en:
                    continue

                link = ''
                link_elem = item.find('link')
                if link_elem is not None:
                    link = link_elem.text if link_elem.text else link_elem.attrib.get('href', '')

                desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}content')
                description_raw = desc_elem.text if desc_elem is not None and desc_elem.text else ''
                details_en = clean_text(description_raw)

                title_ar = translate_to_arabic(title_en)
                details_ar = translate_to_arabic(details_en) if details_en else title_ar
                category = categorize_article(title_en)

                articles.append({
                    "title": title_ar if title_ar else title_en,
                    "title_en": title_en,
                    "details": details_ar if details_ar else details_en,
                    "details_en": details_en if details_en else title_en,
                    "category": category,
                    "image": "https://www.konami.com/games/efootball/common/images/share.png",
                    "link": link if link else KONAMI_INFO_URL,
                    "pubDate": datetime.now().isoformat()
                })
    except Exception as e:
        print(f"Error reading feed {feed_url}: {e}")
    return articles

def fetch_konami_maintenance_notice():
    """خبر إشعارات الصيانة والمشاكل الفنية"""
    return [{
        "title": "إشعار وتحديثات الصيانة وإصلاح الأخطاء الرسمية",
        "title_en": "Official Maintenance & Bug Fix Notice",
        "details": "تابع حالة الصيانة الدورية للسيرفرات وإشعار المشاكل الفنية المكتشفة مباشرة عبر موقع كونامي.",
        "details_en": "Track periodic server maintenance and official technical issue notices from Konami.",
        "category": "maintenance",
        "image": "https://www.konami.com/games/efootball/common/images/share.png",
        "link": KONAMI_INFO_URL,
        "pubDate": datetime.now().isoformat()
    }]

def main():
    all_articles = fetch_konami_maintenance_notice()
    for feed in RSS_FEEDS:
        all_articles.extend(parse_rss_feed(feed))
        time.sleep(1)

    unique_articles = {v['title_en']: v for v in all_articles if v['title']}.values()
    final_list = list(unique_articles)[:15]

    with open('efootball_news.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    print("News successfully aggregated with sub-categories!")

if __name__ == "__main__":
    main()
    

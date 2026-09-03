#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import time
import re
from deep_translator import GoogleTranslator

# مصادر الأخبار المباشرة والتسريبات
RSS_FEEDS = [
    "https://www.konami.com/games/efootball/feed/",
    "https://www.reddit.com/r/eFootball/.rss",
    "https://www.reddit.com/r/pesmobile/.rss"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

DEFAULT_NEWS = [
    {
        "title": "تحديث eFootball v4.0.0 المباشر والتسريبات الجديدة",
        "title_en": "eFootball v4.0.0 Live Update & New Leaks",
        "details": "تابع أحدث تسريبات حزم اللاعبين الإبيك (Epic) ونجوم الأسبوع (POTW) بالإضافة إلى أحداث الفعالية الأسبوعية الخاصة بـ eFootball.",
        "details_en": "Follow the latest Epic card leaks, POTW packs, and weekly event updates for eFootball.",
        "image": "https://www.konami.com/games/efootball/common/images/share.png",
        "link": "https://www.konami.com/games/efootball/",
        "pubDate": datetime.now().isoformat()
    }
]

def translate_text(text):
    if not text or len(text.strip()) == 0:
        return ""
    try:
        clean_text = re.sub('<[^<]+?>', '', text).strip()
        if 'Error 500' in clean_text or 'Server Error' in clean_text:
            return ""
        truncated = clean_text[:500]
        translated = GoogleTranslator(source='auto', target='ar').translate(truncated)
        return translated if translated else clean_text
    except Exception as e:
        print(f"Translation bypassed: {e}")
        return re.sub('<[^<]+?>', '', text).strip()

def extract_image_url(item, description_text):
    try:
        # البحث عن روابط الصور المباشرة داخل الـ XML أو وصف المقال
        for elem in item.iter():
            if 'content' in elem.tag or 'thumbnail' in elem.tag or elem.tag == 'enclosure':
                url = elem.attrib.get('url')
                if url and any(ext in url.lower() for ext in ['.jpg', '.png', '.jpeg', '.webp', 'preview']):
                    return url
        if description_text:
            img_match = re.search(r'src=["\']([^"\']+\.(?:jpg|png|jpeg|webp)[^"\']*)["\']', description_text, re.IGNORECASE)
            if img_match:
                return img_match.group(1)
    except Exception:
        pass
    return "https://www.konami.com/games/efootball/common/images/share.png"

def parse_rss_feed(feed_url):
    articles = []
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            # فحص الوسوم بأسلوب يتوافق مع RSS و Atom (Reddit)
            items = root.findall('.//item')
            if not items:
                # لدعم صيغة Atom الخاصة بـ Reddit
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

            for item in items[:10]:
                # استخراج العنوان
                title_elem = item.find('title')
                if title_elem is None:
                    title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                title_en = title_elem.text if title_elem is not None and title_elem.text else ''

                # استخراج الرابط
                link = ''
                link_elem = item.find('link')
                if link_elem is not None:
                    link = link_elem.text if link_elem.text else link_elem.attrib.get('href', '')
                if not link:
                    link_atom = item.find('{http://www.w3.org/2005/Atom}link')
                    if link_atom is not None:
                        link = link_atom.attrib.get('href', '')

                # استخراج التاريخ
                pubDate = datetime.now().isoformat()
                date_elem = item.find('pubDate') or item.find('{http://www.w3.org/2005/Atom}updated')
                if date_elem is not None and date_elem.text:
                    pubDate = date_elem.text

                # استخراج الوصف التفصيلي
                desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}content')
                description_raw = desc_elem.text if desc_elem is not None and desc_elem.text else ''
                details_en = re.sub('<[^<]+?>', '', description_raw).strip()

                if 'Error 500' in title_en or 'Server Error' in title_en:
                    continue

                image_url = extract_image_url(item, description_raw)

                if title_en and link:
                    title_ar = translate_text(title_en)
                    details_ar = translate_text(details_en) if details_en else title_ar

                    articles.append({
                        "title": title_ar if title_ar else title_en,
                        "title_en": title_en,
                        "details": details_ar if details_ar else details_en,
                        "details_en": details_en if details_en else title_en,
                        "image": image_url,
                        "link": link,
                        "pubDate": pubDate
                    })
    except Exception as e:
        print(f"Error fetching {feed_url}: {e}")
    return articles

def main():
    print("Starting news aggregation...")
    all_articles = []
    
    for feed in RSS_FEEDS:
        articles = parse_rss_feed(feed)
        all_articles.extend(articles)
        time.sleep(1)

    unique_articles = {v['link']: v for v in all_articles}.values()
    final_list = list(unique_articles)

    if not final_list:
        final_list = DEFAULT_NEWS

    with open('efootball_news.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved {len(final_list)} articles!")

if __name__ == "__main__":
    main()
    

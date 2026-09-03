#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import time
import re
import html
from difflib import SequenceMatcher
from deep_translator import GoogleTranslator

# مصادر موثوقة: موقع كونامي الرسمي + حساب تويتر/X الرسمي لـ eFootball عبر Nitter
RSS_FEEDS = [
    "https://www.konami.com/games/efootball/feed/",
    "https://nitter.net/eFootball/rss",
    "https://rsshub.app/twitter/user/eFootball"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    text = re.sub(r'<[^<]+?>', '', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'u/\S+', '', text)
    text = re.sub(r'http\S+', '', text)  # إزالة الروابط النصية داخل التغريدة
    return text.strip()

def is_similar(a, b, threshold=0.75):
    """فحص نسبة تشابه النصوص لمنع تكرار نفس الخبر من تويتر والموقع"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold

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
        print(f"Translation bypass: {e}")
        return clean_text(text)

def extract_image_url(item, description_text):
    try:
        for elem in item.iter():
            if 'content' in elem.tag or 'thumbnail' in elem.tag or elem.tag == 'enclosure':
                url = elem.attrib.get('url')
                if url and any(ext in url.lower() for ext in ['.jpg', '.png', '.jpeg', '.webp']):
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
            
            items = root.findall('.//item')
            if not items:
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

            for item in items[:10]:
                title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                title_en = clean_text(title_elem.text) if title_elem is not None and title_elem.text else ''

                if not title_en or 'Error 500' in title_en or 'Server Error' in title_en or '1500' in title_en:
                    continue

                link = ''
                link_elem = item.find('link')
                if link_elem is not None:
                    link = link_elem.text if link_elem.text else link_elem.attrib.get('href', '')
                if not link:
                    link_atom = item.find('{http://www.w3.org/2005/Atom}link')
                    if link_atom is not None:
                        link = link_atom.attrib.get('href', '')

                pubDate = datetime.now().isoformat()
                date_elem = item.find('pubDate') or item.find('{http://www.w3.org/2005/Atom}updated')
                if date_elem is not None and date_elem.text:
                    pubDate = date_elem.text

                desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}content')
                description_raw = desc_elem.text if desc_elem is not None and desc_elem.text else ''
                details_en = clean_text(description_raw)

                if 'Error 500' in details_en or 'Server Error' in details_en:
                    continue

                image_url = extract_image_url(item, description_raw)
                title_ar = translate_to_arabic(title_en)
                details_ar = translate_to_arabic(details_en) if details_en else title_ar

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
        print(f"Error reading {feed_url}: {e}")
    return articles

def filter_duplicates(articles):
    """فلترة وتصفية الأخبار المكررة بناءً على التشابه والروابط"""
    unique = []
    for article in articles:
        duplicate = False
        for u in unique:
            # فحص تشابه الرابط أو تشابه عنوان الخبر برمجياً
            if article['link'] == u['link'] or is_similar(article['title_en'], u['title_en']):
                duplicate = True
                break
        if not duplicate:
            unique.append(article)
    return unique

def main():
    print("Fetching official eFootball news from Website & Twitter...")
    all_articles = []
    
    for feed in RSS_FEEDS:
        articles = parse_rss_feed(feed)
        all_articles.extend(articles)
        time.sleep(1)

    # تطبيق التصفية لمنع التكرار
    final_list = filter_duplicates(all_articles)[:15]

    if final_list:
        with open('efootball_news.json', 'w', encoding='utf-8') as f:
            json.dump(final_list, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(final_list)} unique official articles!")

if __name__ == "__main__":
    main()
    

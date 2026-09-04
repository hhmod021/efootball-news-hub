#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import re
import html
from deep_translator import GoogleTranslator

# الروابط الرسمية الثلاثة المعتمدة حصراً من شركة KONAMI
URL_UPDATES_AR = "https://konami.com"
URL_UPDATES_EN = "https://konami.com"
URL_MAINTENANCE = "https://konami.com?category=maintenance"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    text = re.sub(r'<[^<]+?>', '', text)
    text = re.sub(r'&#\d+;', ' ', text)
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
    except Exception:
        return clean_text(text)

def fetch_category_news(url, category_type, is_english=False):
    articles = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', res.text, re.DOTALL)
            dates = re.findall(r'(\d{2}/\d{2}/\d{4})', res.text)
            
            for i, title_raw in enumerate(titles[:8]):
                title_clean = clean_text(title_raw)
                if not title_clean or len(title_clean) < 4 or "Error" in title_clean:
                    continue
                
                pub_date = dates[i] if i < len(dates) else datetime.now().strftime("%Y-%m-%d")

                if is_english:
                    title_en = title_clean
                    title_ar = translate_to_arabic(title_clean)
                else:
                    title_ar = title_clean
                    title_en = title_clean

                articles.append({
                    "title": title_ar if title_ar else title_en,
                    "title_en": title_en,
                    "details": f"إعلان رسمي من شركة كونامي: {title_ar}",
                    "details_en": f"Official Konami Announcement: {title_en}",
                    "category": category_type,
                    "image": "https://www.konami.com/games/efootball/common/images/share.png",
                    "link": url,
                    "pubDate": pub_date
                })
    except Exception as e:
        print(f"Error fetching from {url}: {e}")
    return articles

def main():
    print("Fetching news strictly from official KONAMI links...")
    all_articles = []

    # 1. جلب أخبار التحديثات والحملات (العربية والإنجليزية)
    articles_ar = fetch_category_news(URL_UPDATES_AR, "updates", is_english=False)
    articles_en = fetch_category_news(URL_UPDATES_EN, "updates", is_english=True)
    all_articles.extend(articles_ar)
    all_articles.extend(articles_en)

    # 2. جلب أخبار الصيانة والمشاكل التقنية
    articles_maint = fetch_category_news(URL_MAINTENANCE, "maintenance", is_english=False)
    all_articles.extend(articles_maint)

    # إضافة البيانات الافتراضية الرسمية في حال عدم توفر مقالات عاجلة من السيرفر
    if not all_articles:
        all_articles = [
            {
                "title": "تحديثات eFootball الرسمية والحملات الجديدة",
                "title_en": "eFootball Official Updates & Campaigns",
                "details": "تابع أحدث التحديثات اليومية والحملات الخاصة بـ eFootball عبر الموقع الرسمي لشركة Konami.",
                "details_en": "Track daily official updates and campaigns directly from KONAMI website.",
                "category": "updates",
                "image": "https://www.konami.com/games/efootball/common/images/share.png",
                "link": URL_UPDATES_AR,
                "pubDate": datetime.now().isoformat()
            },
            {
                "title": "إشعار وتحديثات الصيانة والمشاكل التقنية",
                "title_en": "Official Maintenance & Technical Notices",
                "details": "تابع حالة السيرفرات المباشرة وإشعار المشاكل الفنية المكتشفة من شركة Konami.",
                "details_en": "Track live server status and official technical notices directly from Konami.",
                "category": "maintenance",
                "image": "https://www.konami.com/games/efootball/common/images/share.png",
                "link": URL_MAINTENANCE,
                "pubDate": datetime.now().isoformat()
            }
        ]

    # منع التكرار بناءً على العنوان
    unique_articles = {v['title_en']: v for v in all_articles if v['title']}.values()
    final_list = list(unique_articles)[:20]

    with open('efootball_news.json', 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    print(f"Successfully updated efootball_news.json with {len(final_list)} items strictly from KONAMI!")

if __name__ == "__main__":
    main()
    

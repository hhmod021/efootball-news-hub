import requests
import json
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import html
from deep_translator import GoogleTranslator

# روابط الـ RSS الخاصة بك (التي تحتوي على التسريبات والأخبار)
KONAMI_INFO_URL = "https://konami.com"
RSS_FEEDS = [
    "https://reddit.com",
    "https://reddit.com"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    # تنظيف وسوم الـ HTML لجعل النص جاهزاً تماماً للقراءة الصوتية في تطبيقك بدون بتر
    text = re.sub(re.compile('<.*?>'), '', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_image_from_content(raw_content):
    """دالة ذكية لسحب رابط أول صورة تظهر في الخبر لعرضها بالتطبيق"""
    if not raw_content:
        return "https://konami.com" # صورة افتراضية في حال عدم وجود صورة
    img_urls = re.findall(r'src=["\'](https://[^"\']+\.(?:jpg|jpeg|png|gif|webp))["\']', raw_content)
    if img_urls:
        return img_urls[0]
    return "https://konami.com"

def translate_text(text, target_lang='ar'):
    """ترجمة النصوص بدقة وحماية من أخطاء السيرفر"""
    if not text:
        return ""
    try:
        # تقصير النص للترجمة إذا كان ضخماً جداً لتفادي حظر المترجم، لكن يظل الخبر الأصلي كاملاً
        clean_txt = clean_text(text)[:1000]
        if "Error 500" in clean_txt or "Server Error" in clean_txt:
            return ""
        translated = GoogleTranslator(source='auto', target=target_lang).translate(clean_txt)
        return translated if translated else clean_text(text)
    except Exception as e:
        return clean_text(text)

def categorize_article(title, content):
    """تصنيف تلقائي مبني على فحص الكلمات المفتاحية في العنوان والمحتوى"""
    title_lower = title.lower() + content.lower()
    maintenance_keywords = ['maintenance', 'issue', 'fix', 'notice', 'server', 'صيانة', 'إصلاح', 'عطل', 'توقف']
    
    if any(k in title_lower for k in maintenance_keywords):
        return "maintenance_and_fixes" # التبويب الثاني
    return "updates_and_additions" # التبويب الأول

def parse_rss_feed(feed_url):
    articles = []
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            # التعامل مع صيغ XML المختلفة (Atom و RSS)
            namespaces = {'atom': 'http://w3.org'}
            items = root.findall('.//atom:entry', namespaces) if 'entry' in response.text else root.findall('.//item')
            
            for item in items[:10]:
                title_elem = item.find('atom:title', namespaces) if item.find('atom:title', namespaces) is not None else item.find('title')
                if title_elem is None:
                    continue
                    
                title_en = clean_text(title_elem.text)
                
                # جلب الرابط
                link_elem = item.find('atom:link', namespaces) if item.find('atom:link', namespaces) is not None else item.find('link')
                link = link_elem.get('href') if link_elem is not None and link_elem.get('href') else (link_elem.text if link_elem is not None else KONAMI_INFO_URL)
                
                # جلب محتوى الخبر الكامل "من دهوك للبصرة" بدون بتر
                desc_elem = item.find('atom:content', namespaces) or item.find('atom:summary', namespaces) or item.find('description')
                raw_content = desc_elem.text if desc_elem is not None else ""
                content_en = clean_text(raw_content)
                
                # استخراج الصورة المصغرة للخبر
                image_url = extract_image_from_content(raw_content)
                
                # الترجمة للغة العربية لتجهيزها مسبقاً للتطبيق
                title_ar = translate_text(title_en, 'ar')
                content_ar = translate_text(content_en, 'ar')
                
                category = categorize_article(title_en, content_en)
                
                articles.append({
                    "title_en": title_en,
                    "title_ar": title_ar,
                    "content_en": content_en,
                    "content_ar": content_ar,
                    "image": image_url,
                    "link": link,
                    "category": category,
                    "pubDate": datetime.now().isoformat()
                })
    except Exception as e:
        print(f"Error reading feed {feed_url}: {e}")
    return articles

def fetch_konami_maintenance_notice():
    """جلب إشعار صيانة افتراضي أو محاكي من موقع كونامي ليذهب دائماً لقسم الصيانة"""
    return [{
        "title_en": "Official Maintenance & Bug Fix Notice",
        "title_ar": "إشعار الصيانة الدورية وإصلاح الأخطاء الرسمية",
        "content_en": "Track periodic server maintenance, live updates, and official technical fixes directly from KONAMI servers.",
        "content_ar": "متابعة أعمال الصيانة الدورية للسيرفرات، التحديثات المباشرة، والإصلاحات التقنية الرسمية القادمة من شركة كونامي.",
        "image": "https://konami.com",
        "link": KONAMI_INFO_URL,
        "category": "maintenance_and_fixes",
        "pubDate": datetime.now().isoformat()
    }]

def main():
    all_articles = fetch_konami_maintenance_notice()
    
    for feed in RSS_FEEDS:
        all_articles.extend(parse_rss_feed(feed))
        time.sleep(1) # لتفادي الحظر أثناء السحب
        
    # تصفية العناصر المكررة بناءً على العنوان الإنجليزي
    unique_articles = {v['title_en']: v for v in all_articles}.values()
    
    # بناء الهيكل النهائي المترجم والمصنف بدقة تامة حسب طلبك وحسب لغة التطبيق
    final_output = {
        "ar": {
            "updates_and_additions": [],
            "maintenance_and_fixes": []
        },
        "en": {
            "updates_and_additions": [],
            "maintenance_and_fixes": []
        }
    }
    
    for art in list(unique_articles)[:20]:
        cat = art["category"]
        
        # ملء قسم اللغة العربية في الـ JSON
        final_output["ar"][cat].append({
            "title": art["title_ar"],
            "content": art["content_ar"],
            "image": art["image"],
            "link": art["link"],
            "date": art["pubDate"]
        })
        
        # ملء قسم اللغة الإنجليزية في الـ JSON
        final_output["en"][cat].append({
            "title": art["title_en"],
            "content": art["content_en"],
            "image": art["image"],
            "link": art["link"],
            "date": art["pubDate"]
        })
        
    # حفظ الهيكل الجديد ليكون جاهزاً 100% لتطبيقك ليقرأ منه مباشرة
    with open('efootball_news.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
        
    print("News successfully aggregated with images and sub-categories!")

if __name__ == "__main__":
    main()
    

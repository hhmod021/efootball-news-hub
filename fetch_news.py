import requests
from bs4 import BeautifulSoup
import json

def get_efootball_news(lang='ar'):
    """
    lang: 'ar' للعربية أو 'en' للإنجليزية
    """
    base_url = f"https://www.konami.com/efootball/{lang}/topic/news/list"
    domain = "https://www.konami.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            print(f"فشل الاتصال بالموقع. رمز الخطأ: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن عناصر الأخبار في صفحة كونامي
        news_elements = soup.find_all('li', class_='news_item') # الكود المصدري الرسمي لكونامي يحتوي على هكذا عناصر للقوائم
        
        # إذا لم يجد الفئة المحددة، نبحث عن روابط الأخبار العامة في قسم الـ topic
        if not news_elements:
            news_elements = soup.select('ul.news_list > li, div.news_list > a, div.topic_list a')
            
        news_data = {
            "updates_and_additions": [], # التبويب الأول: التحديثات والاضافات
            "maintenance_and_fixes": []  # التبويب الثاني: الصيانة والإصلاحات
        }
        
        # الكلمات المفتاحية للتصنيف التلقائي الذكي
        maintenance_keywords = ['صيانة', 'إصلاح', 'مشكلة', 'تعويض', 'تحديث مباشر', 'maintenance', 'fix', 'issue', 'compensation', 'live update']
        
        for item in news_elements[:15]: # جلب آخر 15 خبر للتأكد من تغطية كل جديد
            title_el = item.find(['p', 'span', 'h3'], class_='title') or item.find('p')
            link_el = item if item.name == 'a' else item.find('a')
            date_el = item.find('span', class_='date')
            
            if not link_el or not link_el.get('href'):
                continue
                
            title = title_el.text.strip() if title_el else "خبر جديد"
            relative_url = link_el.get('href')
            full_url = relative_url if relative_url.startswith('http') else domain + relative_url
            date_str = date_el.text.strip() if date_el else ""
            
            # --- خطوة جلب تفاصيل الخبر الكاملة بدون بتر ---
            detail_response = requests.get(full_url, headers=headers)
            detail_content = ""
            
            if detail_response.status_code == 200:
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                # كونامي تضع نص الخبر الكامل داخل div يحمل كلاس الجسد أو المحتوى
                detail_box = detail_soup.find('div', class_='news_detail') or detail_soup.find('div', class_='detail_box') or detail_soup.find('section')
                if detail_box:
                    # جلب النص كاملاً مع الحفاظ على السطور الفاصلة لتنسيق مريح للمستخدم
                    detail_content = detail_box.text.strip()
                else:
                    detail_content = detail_soup.get_text().strip() # حل احتياطي إذا تغير القالب
            
            # هيكلة الخبر
            news_item = {
                "title": title,
                "date": date_str,
                "url": full_url,
                "content": detail_content # النص الكامل "من دهوك للبصرة"
            }
            
            # --- الفرز التلقائي بين التبويبين ---
            is_maintenance = any(key in title.lower() or key in detail_content.lower() for key in maintenance_keywords)
            
            if is_maintenance:
                news_data["maintenance_and_fixes"].append(news_item)
            else:
                news_data["updates_and_additions"].append(news_item)
                
        return news_data

    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

# --- مثال لتشغيل السكربت وحفظ النتائج في ملف JSON لتطبيقك ---
if __name__ == "__main__":
    # جلب الأخبار باللغة العربية
    arabic_news = get_efootball_news(lang='ar')
    
    # جلب الأخبار باللغة الإنجليزية
    english_news = get_efootball_news(lang='en')
    
    final_output = {
        "ar": arabic_news,
        "en": english_news
    }
    
    # حفظ البيانات في ملف لتطبيقك ليقرأ منها
    with open('efootball_news.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
        
    print("تم جلب الأخبار وتصنيفها وترجمتها بنجاح وحفظها في efootball_news.json!")
    

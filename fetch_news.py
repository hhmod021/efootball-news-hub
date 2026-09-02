#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime
from xml.etree import ElementTree as ET
import time

# RSS feed sources for eFootball news, Konami updates, and gaming leaks
RSS_FEEDS = [
    "https://www.konami.com/games/efootball/feed/",
    "https://www.reddit.com/r/eFootball/.rss",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.gameinformer.com/",
    "https://www.ign.com/rss/games",
    "https://www.polygon.com/rss/index.xml",
    "https://www.kotaku.com/rss",
]

# Custom headers to bypass rate-limiting and blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def fetch_rss_feed(url, timeout=10):
    """Fetch RSS feed with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        print(f"Timeout fetching {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Connection error fetching {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def parse_rss_feed(rss_content):
    """Parse RSS feed XML and extract articles"""
    articles = []
    try:
        root = ET.fromstring(rss_content)
        
        # Handle both RSS and Atom feeds
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items:
            article = {}
            
            # Extract title
            title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
            article['title'] = title_elem.text if title_elem is not None and title_elem.text else 'Untitled'
            
            # Extract link
            link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
            if link_elem is not None:
                if link_elem.text:
                    article['link'] = link_elem.text
                elif link_elem.get('href'):
                    article['link'] = link_elem.get('href')
                else:
                    article['link'] = ''
            else:
                article['link'] = ''
            
            # Extract publication date
            pub_date_elem = item.find('pubDate') or item.find('{http://www.w3.org/2005/Atom}published')
            article['pubDate'] = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else datetime.now().isoformat()
            
            if article['title'] and article['link']:
                articles.append(article)
    except ET.ParseError as e:
        print(f"XML parsing error: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error parsing RSS feed: {str(e)}")
        return []
    
    return articles

def fetch_all_news():
    """Fetch news from all RSS feeds with retry logic"""
    all_articles = []
    
    for feed_url in RSS_FEEDS:
        print(f"Fetching from: {feed_url}")
        rss_content = fetch_rss_feed(feed_url)
        
        if rss_content:
            articles = parse_rss_feed(rss_content)
            all_articles.extend(articles)
            print(f"  - Retrieved {len(articles)} articles")
        
        time.sleep(1)  # Be respectful to servers
    
    # Remove duplicates while preserving order
    seen = set()
    unique_articles = []
    for article in all_articles:
        article_key = (article['title'], article['link'])
        if article_key not in seen:
            seen.add(article_key)
            unique_articles.append(article)
    
    return unique_articles

def load_fallback_data():
    """Load fallback data from existing efootball_news.json"""
    fallback_file = 'efootball_news.json'
    if os.path.exists(fallback_file):
        try:
            with open(fallback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print(f"Error loading fallback data: {str(e)}")
    
    # Default fallback data
    return [
        {
            "title": "eFootball Official Site",
            "link": "https://www.konami.com/games/efootball/",
            "pubDate": datetime.now().isoformat()
        },
        {
            "title": "eFootball News Hub - No data available",
            "link": "https://github.com/hhmod021/efootball-news-hub",
            "pubDate": datetime.now().isoformat()
        }
    ]

def save_news_to_json(articles):
    """Save articles to efootball_news.json with fallback protection"""
    output_file = 'efootball_news.json'
    
    try:
        # Ensure we have data
        if not articles or len(articles) == 0:
            print("No articles fetched, using fallback data...")
            articles = load_fallback_data()
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(articles)} articles to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving to {output_file}: {str(e)}")
        # Attempt recovery with fallback
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(load_fallback_data(), f, indent=2, ensure_ascii=False)
            print("Fallback data saved successfully")
            return True
        except Exception as recovery_error:
            print(f"Critical error - could not save file: {str(recovery_error)}")
            return False

def main():
    """Main execution"""
    print("Starting eFootball News Fetcher...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    articles = fetch_all_news()
    print(f"\nTotal unique articles fetched: {len(articles)}")
    
    success = save_news_to_json(articles)
    
    if success:
        print("\n✓ Fetch operation completed successfully")
    else:
        print("\n✗ Fetch operation encountered critical errors")
        exit(1)

if __name__ == '__main__':
    main()

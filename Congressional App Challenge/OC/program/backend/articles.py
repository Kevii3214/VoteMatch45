import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_article_urls(url, depth=1):
    visited = set()
    to_visit = [url]
    article_urls = set()

    for _ in range(depth):
        next_to_visit = []
        for page_url in to_visit:
            if page_url in visited:
                continue
            visited.add(page_url)

            try:
                response = requests.get(page_url, timeout=5)
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link['href']
                    full_url = requests.compat.urljoin(url, href)
                    
                    if re.search(r'45th congressional|Michelle Steel|Derek Tran|Adam Schiff|Steve Garvey|Proposition 2|Proposition 3|Proposition 4|Proposition 5|Proposition 6|Proposition 32|Proposition 33|Proposition 34|Proposition 35|Proposition 36', link.text, re.IGNORECASE):
                        article_urls.add(full_url)
                    elif full_url.startswith(url) and full_url not in visited:
                        next_to_visit.append(full_url)
            except Exception as e:
                print(f"Error fetching {page_url}: {str(e)}")

        to_visit = next_to_visit

    return list(article_urls)

def fetch_article_content(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1').text if soup.find('h1') else 'No title found'
        content = ''
        article_body = soup.find('article') or soup.find('div', class_='article-body') or soup.find('div', class_='story-body')
        if article_body:
            paragraphs = article_body.find_all('p')
            content = ' '.join([p.text for p in paragraphs])
        
        # Filter for content only for 45th congressional district
        relevant_terms = r'45th congressional|Michelle Steel|Derek Tran'
        if not re.search(relevant_terms, content, re.IGNORECASE):
            return None
        
        date = None
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            date = date_meta['content']
        else:
            date_element = soup.find('time') or soup.find('span', class_='date')
            if date_element:
                date = date_element.text
        
        if date:
            try:
                date = datetime.strptime(date[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                date = None
        
        return title, content, date, url
    except Exception as e:
        print(f"Error fetching article content from {url}: {str(e)}")
        return None

def scrape_45th_district_news():
    news_sites = [
        'https://www.ocregister.com/',
        'https://voiceofoc.org/',
        'https://www.latimes.com/california/orange-county',
        'https://apnews.com/hub/california',
        'https://www.reuters.com/news/us/california/',
        'https://www.npr.org/sections/national/',
        'https://www.bbc.com/news/world/us_and_canada'
    ]
    
    all_articles = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(get_article_urls, site, 2): site for site in news_sites}
        for future in as_completed(future_to_url):
            site = future_to_url[future]
            try:
                article_urls = future.result()
                futures = [executor.submit(fetch_article_content, url) for url in article_urls]
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        title, content, date, url = result
                        if date is not None:
                            all_articles.append({
                                'title': title,
                                'content': content,
                                'url': url,
                                'date': date
                            })
            except Exception as e:
                print(f"Error scraping {site}: {str(e)}")
    
    all_articles.sort(key=lambda x: x['date'], reverse=True)
    return all_articles

def return_articles(articles):
    if not articles:
        return "No articles found."
    else:
        titles, dates, urls, contents = [], [], [], []
        for article in articles[:3]:  # Limit to first 3 articles
            titles.append(article['title'])
            dates.append(article['date'])
            urls.append(article['url'])
            contents.append(article['content'][:200] + "...")  # First 200 characters
        return titles, dates, urls, contents
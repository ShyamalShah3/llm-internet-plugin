import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# Get the number of pages to search from environment variable, default to 5 if not set
PAGES_TO_SEARCH = int(os.environ.get('PAGES_TO_SEARCH', 5))

def handler(event, context):
    # Extract search query from the event
    search_query = event['query']

    # Perform search
    search_results = perform_search(search_query)

    # Scrape results
    scraped_results = []
    for result in search_results:
        if len(scraped_results) >= PAGES_TO_SEARCH:
            break
        scraped_content = scrape_website(result['link'])
        if scraped_content:  # Only add successful scrapes
            scraped_results.append({
                'title': result['title'],
                'url': result['link'],
                'content': scraped_content
            })

    # Prepare the response
    response = {
        'statusCode': 200,
        'body': {
            'query': search_query,
            'results': scraped_results
        },
        'headers': {
            'Content-Type': 'application/json'
        }
    }

    # Return the results as a JSON-serializable dictionary
    return response

def perform_search(query):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for result in soup.find_all('div', class_='result__body'):
            title = result.find('a', class_='result__a')
            snippet = result.find('a', class_='result__snippet')
            link = result.find('a', class_='result__url')
            if title and snippet and link:
                results.append({
                    'title': title.text.strip(),
                    'snippet': snippet.text.strip(),
                    'link': link.get('href')
                })
        return results
    except Exception as e:
        print(f"Error performing search: {str(e)}")
        return []

def scrape_website(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Limit text to ~1000 words to avoid excessively large responses
        words = text.split()
        if len(words) > 1000:
            text = ' '.join(words)

        return text
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None  # Return None for failed scrapes
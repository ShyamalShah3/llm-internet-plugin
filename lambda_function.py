import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def handler(event, context):
    # Extract search query from the event
    search_query = event['query']

    # Perform search
    search_results = perform_search(search_query)

    # Scrape top 3 results
    scraped_results = []
    for result in search_results[:3]:
        scraped_content = scrape_website(result['link'])
        scraped_results.append({
            'title': result['title'],
            'url': result['link'],
            'snippet': result['snippet'],
            'content': scraped_content
        })

    # Prepare the response in a JSON-serializable format
    response = {
        'query': search_query,
        'results': scraped_results
    }

    # Return the results
    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            'Content-Type': 'application/json'
        }
    }

def perform_search(query):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    for result in soup.find_all('div', class_='result__body')[:3]:  # Limit to top 3 results
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
        return f"Error scraping {url}: {str(e)}"
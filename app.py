import json
import requests
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    # Extract search query from the event
    search_query = event['query']

    # Perform internet search
    search_results = perform_search(search_query)

    # Process and summarize the search results
    summary = summarize_results(search_results)

    # Return the summarized results
    return {
        'statusCode': 200,
        'body': json.dumps({'summary': summary})
    }

def perform_search(query):
    # Use DuckDuckGo search API
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract relevant information from the search results
    results = []
    for result in soup.find_all('div', class_='result__body')[:5]:  # Limit to top 5 results
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

def summarize_results(results):
    # This is a simple concatenation of results
    # In a real-world scenario, you might want to use an LLM to generate a more coherent summary
    summary = ""
    for result in results:
        summary += f"Title: {result['title']}\n"
        summary += f"Snippet: {result['snippet']}\n"
        summary += f"Link: {result['link']}\n\n"

    return summary

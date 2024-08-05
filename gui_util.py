import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random
import re
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Initialize sentiment analysis
analyzer = SentimentIntensityAnalyzer()

# Google Custom Search API key and Search Engine ID
API_KEY = "AIzaSyDNmDWsei3Fkr1eJF16ARKFWHxlLXyAkzQ"
SEARCH_ENGINE_ID = "f50acf0b91bf54f03"  # Replace with your actual Search Engine ID


def scrape_news(country, categories):
    articles = []
    for category in categories:
        url = f"https://news.google.com/rss/search?q={category}+{country}&hl=en-KE&gl=KE&ceid=KE:en"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item'):
                title = item.find('title').text if item.find('title') else 'No Title'
                link = item.find('link').text if item.find('link') else 'No Link'
                pub_date_str = item.find('pubDate').text if item.find('pubDate') else ''
                image = item.find('media:thumbnail')['url'] if item.find('media:thumbnail') else None
                description = item.find('description').text if item.find('description') else 'No Description'

                try:
                    pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                except ValueError:
                    pub_date = datetime.min  # Use a minimal date if parsing fails

                # Filter for articles published in the last 7 days
                if pub_date > datetime.now() - timedelta(days=7):
                    articles.append({
                        'title': title,
                        'link': link,
                        'publishedAt': pub_date,
                        'image': image,
                        'description': description
                    })
        except requests.RequestException as e:
            print(f"Error fetching news: {e}")

    return pd.DataFrame(articles)


def analyze_sentiment(text):
    if text:
        score = analyzer.polarity_scores(text)['compound']
        if score >= 0.05:
            return 'Positive: The sentiment of the text is generally positive.'
        elif score <= -0.05:
            return 'Negative: The sentiment of the text is generally negative.'
        else:
            return 'Neutral: The sentiment of the text is neutral.'
    return 'Neutral: The sentiment of the text is neutral.'


def extract_entities(text):
    if text:
        # Dummy entity extraction for demonstration
        entities = {'PERSON': ['Example Person']}  # Simplified extraction
        return entities
    return {}


def fetch_related_information(entities):
    related_info = []
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            search_query = f"{entity} background information"
            url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&key={API_KEY}&cx={SEARCH_ENGINE_ID}&num=5"

            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an error for bad responses
                search_results = response.json()
                for item in search_results.get('items', []):
                    title = item.get('title', 'No Title')
                    link = item.get('link', 'No Link')
                    snippet = item.get('snippet', 'No Description')
                    image = None  # Google Custom Search API does not provide direct image links in search results

                    related_info.append({
                        'title': title,
                        'link': link,
                        'publishedAt': datetime.now(),  # Placeholder, as pubDate is not provided by the API
                        'image': image,
                        'description': snippet
                    })
            except requests.RequestException as e:
                print(f"Error fetching related information: {e}")

    # Return the best five related articles
    return pd.DataFrame(related_info).head(5)


def plot_sector_impact(impact_scores):
    fig, ax = plt.subplots()
    sectors = list(impact_scores.keys())
    scores = list(impact_scores.values())

    ax.bar(sectors, scores, color='skyblue')
    ax.set_xlabel('Sectors')
    ax.set_ylabel('Impact Score')
    ax.set_title('Impact of News on Different Sectors')
    ax.set_ylim([-1, 1])  # Ensure the graph fits well within the range of -1 to 1

    for i, v in enumerate(scores):
        ax.text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom')

    # Save to a BytesIO object and encode as base64
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    plt.close(fig)
    return img_str


def analyze_sector_impact(text):
    # Define sectors with random initial impact scores
    sectors = {
        'Technology': random.uniform(-1, 1),
        'Finance': random.uniform(-1, 1),
        'Healthcare': random.uniform(-1, 1),
        'Energy': random.uniform(-1, 1),
        'Retail': random.uniform(-1, 1)
    }

    # Define keywords associated with each sector
    keywords = {
        'Technology': ['innovation', 'tech', 'gadgets', 'software', 'hardware'],
        'Finance': ['investment', 'stocks', 'banking', 'economy', 'financial'],
        'Healthcare': ['medicine', 'hospital', 'health', 'wellness', 'disease'],
        'Energy': ['oil', 'gas', 'renewable', 'energy', 'power'],
        'Retail': ['shopping', 'consumer', 'sales', 'market', 'merchandise']
    }

    # Adjust sector scores based on keyword matches in the text
    for sector, words in keywords.items():
        for word in words:
            if re.search(r'\b' + word + r'\b', text, re.IGNORECASE):
                sectors[sector] += 1

    # Normalize scores to ensure they are proportionate
    max_score = max(sectors.values()) if max(sectors.values()) > 0 else 1
    normalized_scores = {k: v / max_score for k, v in sectors.items()}

    return normalized_scores

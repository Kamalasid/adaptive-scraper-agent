"""
ADAPTIVE WEB SCRAPER AGENT
"""

import requests
from bs4 import BeautifulSoup
import json
import anthropic
import os


class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
    
    def __str__(self):
        return f"{self.name} - {self.price}"


def fetch_webpage(url):
    print(f"Fetching: {url}")
    headers = {"User-Agent": "Mozilla/5.0 Chrome/91.0"}
    response = requests.get(url, headers=headers, timeout=10)
    return response.text


def extract_products(html, container_selector, name_selector, price_selector):
    print(f"Looking for products with selector: {container_selector}")
    
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.select(container_selector)
    print(f"Found {len(containers)} containers")
    
    if len(containers) == 0:
        return None, "No containers found with that selector"
    
    products = []
    for container in containers:
        name_elem = container.select_one(name_selector)
        name = name_elem.get_text(strip=True) if name_elem else None
        
        price_elem = container.select_one(price_selector)
        price = price_elem.get_text(strip=True) if price_elem else None
        
        if name and price:
            products.append(Product(name, price))
    
    if len(products) == 0:
        return None, "Found containers but couldn't extract name/price"
    
    return products, None


def ask_ai_to_fix(html_snippet, current_selectors, error_message):
    print("Asking AI to analyze the problem...")
    
    client = anthropic.Anthropic()
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are a web scraping expert. My scraper broke.

CURRENT SELECTORS I TRIED:
- Container: {current_selectors['container']}
- Name: {current_selectors['name']}  
- Price: {current_selectors['price']}

ERROR: {error_message}

HERE'S THE HTML (first 3000 characters):
```html
{html_snippet[:3000]}
```

Analyze the HTML and tell me the correct CSS selectors.

RESPOND WITH ONLY THIS JSON (no other text):
{{
    "container": "selector for each product container",
    "name": "selector for product name",
    "price": "selector for price"
}}
"""
        }]
    )
    
    response_text = message.content[0].text.strip()
    
    if "```" in response_text:
        lines = response_text.split("\n")
        response_text = "\n".join(line for line in lines if not line.startswith("```"))
    
    new_selectors = json.loads(response_text)
    print(f"AI suggests:")
    print(f"   Container: {new_selectors['container']}")
    print(f"   Name: {new_selectors['name']}")
    print(f"   Price: {new_selectors['price']}")
    
    return new_selectors


def run_agent(url, initial_selectors, max_retries=3):
    print("")
    print("=" * 50)
    print("ADAPTIVE SCRAPER AGENT STARTING")
    print("=" * 50)
    
    current_selectors = initial_selectors.copy()
    html = None
    
    for attempt in range(1, max_retries + 1):
        print("")
        print(f"ATTEMPT {attempt} of {max_retries}")
        print("-" * 30)
        
        if html is None:
            try:
                html = fetch_webpage(url)
            except Exception as e:
                print(f"Couldn't fetch webpage: {e}")
                return None
        
        products, error = extract_products(
            html,
            current_selectors['container'],
            current_selectors['name'],
            current_selectors['price']
        )
        
        if products:
            print(f"SUCCESS! Found {len(products)} products!")
            return products
        
        print(f"Failed: {error}")
        
        if attempt < max_retries:
            try:
                new_selectors = ask_ai_to_fix(html, current_selectors, error)
                current_selectors = new_selectors
                print("Retrying with new selectors...")
            except Exception as e:
                print(f"AI couldn't help: {e}")
    
    print(f"Agent gave up after {max_retries} attempts")
    return None


if __name__ == "__main__":
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("")
        print("NO API KEY FOUND!")
        print("")
        print("To use this agent:")
        print("1. Go to: https://console.anthropic.com/")
        print("2. Sign up and create an API key")
        print("3. In your terminal, run:")
        print("")
        print('   set ANTHROPIC_API_KEY=your-key-here')
        print("")
        print("4. Then run: python agent.py")
        print("")
    else:
        url = "https://books.toscrape.com/"
        
        initial_selectors = {
            "container": "article.product_pod",
            "name": "h3 a",
            "price": ".price_color"
        }
        
        products = run_agent(url, initial_selectors)
        
        if products:
            print("")
            print("EXTRACTED PRODUCTS:")
            print("=" * 50)
            for i, product in enumerate(products[:10], 1):
                print(f"{i}. {product}")

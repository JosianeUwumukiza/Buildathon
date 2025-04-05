from flask import Flask, request, jsonify, render_template
import requests
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from recommendation import get_final_recommendation


app = Flask(__name__)

# === LOAD ENV VARS ===
load_dotenv()
EXA_API_KEY = os.getenv("EXA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

if not EXA_API_KEY or not OPENAI_API_KEY or not SCRAPER_API_KEY:
    raise ValueError("Missing one or more required API keys in your .env file.")

# Create OpenAI client with the new interface
client = OpenAI(api_key=OPENAI_API_KEY)

# Define headers for the Exa Search API
exa_headers = {
    "Authorization": f"Bearer {EXA_API_KEY}",
    "Content-Type": "application/json"
}

def search_exa(query):
    exa_search_url = "https://api.exa.ai/search"
    exa_payload = {"query": query, "numResults": 6}
    response = requests.post(exa_search_url, headers=exa_headers, json=exa_payload)
    response.raise_for_status()
    data = response.json()
    # Extract URLs from the "results" key using the "id" field
    results = data.get("results", [])
    urls = [result.get("id") for result in results if result.get("id")]
    return urls

def crawl_url(url):
    # Use ScraperAPI to bypass anti-crawling measures
    scraper_url = "http://api.scraperapi.com/"
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": "true"
    }
    response = requests.get(scraper_url, params=params)
    response.raise_for_status()
    return response.text

def get_openai_summary(content, url):
    # Build a prompt that includes a snippet of the page content (limit to 4000 characters) and the URL
    prompt = (
        f"Extract the product name and price from the following web page text. "
        f"Return a 1-2 sentence summary that includes the product name, price (if found), and the link: {url}\n\n"
        f"{content[:4000]}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a smart price extraction assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"Failed to extract information: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def estimate():
    if request.method == "POST":
        # Use the item description as the query
        description = request.form.get("description", "")
        query = description
        try:
            urls = search_exa(query)
            if not urls:
                return render_template("result.html", error="No valid URLs found in Exa Search API response.")
            
            # Crawl each URL using ScraperAPI
            crawl_results = []
            for url in urls:
                try:
                    content = crawl_url(url)
                    crawl_results.append({"url": url, "content": content})
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
                    continue
            
            if not crawl_results:
                return render_template("result.html", error="Failed to crawl all URLs.")
            
            # Generate summaries using OpenAI
            summaries = []
            for page in crawl_results:
                summary = get_openai_summary(page['content'], page['url'])
                summaries.append({
                    "url": page['url'],
                    "summary": summary
                })
            final_price = get_final_recommendation(summaries)
            # Return the results page with individual summaries and final recommendation
            return render_template("result.html", summaries=summaries, final_price=final_price)
        except Exception as e:
            return render_template("result.html", error=str(e))
    
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)

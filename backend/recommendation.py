from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables and set up OpenAI client
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in your .env file")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_final_recommendation(summaries):
    """
    Accepts a list of summaries (each a dict with keys 'url' and 'summary') 
    and returns a final recommended price to list the item at.
    """
    # Aggregate the individual website summaries into bullet points
    aggregated_info = "\n".join([f"- {s['summary']}" for s in summaries])
    prompt = (
        f"Based on the following website recommendations for pricing this item, "
        f"what is the best price to list the item at? Please return just the recommended price in dollars.\n\n"
        f"{aggregated_info}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a pricing recommendation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        final_price = response.choices[0].message.content.strip()
        return final_price
    except Exception as e:
        return f"Failed to generate final recommendation: {str(e)}"

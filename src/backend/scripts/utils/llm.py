from groq import Groq
import os
import dotenv

dotenv.load_dotenv()

API_KEY = os.getenv("API_KEY")
client = Groq(api_key=API_KEY)

def needs_citation(query: str) -> bool:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # free + fast
        max_tokens=5,
        temperature=0,
        messages=[{
            "role": "user",
            "content": f"Does this statement make a factual claim that requires evidence or a reference to verify? Answer YES or NO only.\nStatement: {query}"
        }]
    )
    return response.choices[0].message.content.strip().upper() == "YES"

if __name__ == "__main__":
    query = "Our model performed slightly better than the pretrained SciBERT"

    print(needs_citation(query))
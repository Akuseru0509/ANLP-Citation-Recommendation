from groq import Groq
import os
import dotenv

dotenv.load_dotenv()

API_KEY = os.getenv("API_KEY")
client = Groq(api_key=API_KEY)

def needs_citation(query: str) -> bool:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=5,
        temperature=0,
        messages=[{
            "role": "user",
            "content": f"Does this statement make a factual claim that requires evidence or a reference to verify? Answer YES or NO only.\nStatement: {query}"
        }]
    )

    return response.choices[0].message.content.strip().upper() == "YES"

def get_summary(result: dict):
    prompt = f"""You are a scientific paper assistant.
        Given the abstract of a retrieved paper, write a concise summary capturing its key findings.

        Abstract:
        {result.get("abstract")}

        Write a 3-4 sentence summary that:
        - Captures the key findings, methods, and conclusions
        - Uses precise scientific language

    Summary:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=200,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()

def summarize(query, results: list[dict]) -> list[dict]:
    for i in range(0, len(results)):
        results[i].add({
            "summary": get_summary(query, results[i])
        })

    return results
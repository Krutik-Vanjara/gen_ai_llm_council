import asyncio
import httpx
import time
import re
from fastapi import FastAPI
from pydantic import BaseModel
from .config import COUNCIL_MEMBERS, CHAIRMAN

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


async def ask_ollama_with_metrics(client: httpx.AsyncClient, url: str, model: str, prompt: str, role: str):
    """
    role: A label for logging (e.g., 'Council_1' or 'Chairman')
    """
    endpoint = f"{url.rstrip('/')}/api/generate"
    print(f"DEBUG: Sending request to {role} ({model}) at {url}...")
    start = time.perf_counter()

    try:
        payload = {"model": model, "prompt": prompt, "stream": False}
        # Timeout remains 180s for heavy synthesis
        response = await client.post(endpoint, json=payload, timeout=180.0)
        latency = (time.perf_counter() - start)

        resp_json = response.json()
        content = resp_json.get("response", "").strip()

        if not content:
            print(f"⚠️  {role} returned an empty response.")
            return {"response": "Error: Empty response.", "latency": round(latency, 2)}

        print(f"✅ {role} completed in {latency:.2f}s")
        return {"response": content, "latency": round(latency, 2)}

    except Exception as e:
        print(f"❌ {role} FAILED: {str(e)}")
        return {"response": f"Offline: {str(e)}", "latency": 0}


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    overall_start = time.time()
    query = request.message
    print("\n" + "=" * 50)
    print(f"🚀 NEW COUNCIL SESSION STARTED")
    print(f"User Query: {query}")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        # --- STAGE 1: Parallel Opinions ---
        print("\n--- STAGE 1: Gathering Initial Opinions ---")
        node_names = list(COUNCIL_MEMBERS.keys())
        tasks = [
            ask_ollama_with_metrics(client, m["url"], m["model"], query, name)
            for name, m in COUNCIL_MEMBERS.items()
        ]
        results = await asyncio.gather(*tasks)
        opinions = {node_names[i]: results[i] for i in range(len(node_names))}

        # --- STAGE 2: Peer Review (Ring Logic) ---
        print("\n--- STAGE 2: Peer Review & Ranking (Ring Logic) ---")
        review_tasks = []
        for i in range(len(node_names)):
            reviewer_name = node_names[i]
            # Ring Logic: 1 reviews 2, 2 reviews 3, 3 reviews 1
            peer_name = node_names[(i + 1) % len(node_names)]

            peer_answer = opinions[peer_name]["response"]

            review_prompt = (
                f"Critique this answer: '{peer_answer}'. "
                f"Your first line MUST be: 'Rating: X/10'. Then explain why."
            )

            review_tasks.append(
                ask_ollama_with_metrics(
                    client,
                    COUNCIL_MEMBERS[reviewer_name]["url"],
                    COUNCIL_MEMBERS[reviewer_name]["model"],
                    review_prompt,
                    f"Reviewer:{reviewer_name}"
                )
            )

        review_results = await asyncio.gather(*review_tasks)

        reviews = {}
        for i, name in enumerate(node_names):
            raw_text = review_results[i]["response"]
            match = re.search(r"Rating:\s*(\d+)", raw_text)
            score = int(match.group(1)) if match else "N/A"

            reviews[name] = {
                "response": raw_text,
                "score": score,
                "latency": review_results[i]["latency"],
                "reviewing": node_names[(i + 1) % len(node_names)]
            }

        # --- STAGE 3: Chairman Synthesis ---
        print("\n--- STAGE 3: Chairman Synthesis (Final Phase) ---")
        opinion_ctx = "\n\n".join([f"{n}: {r['response']}" for n, r in opinions.items()])
        review_ctx = "\n\n".join([f"Review from {n}: {r['response']}" for n, r in reviews.items()])

        chair_prompt = (
            f"You are the Council Chairman. Synthesis the following research.\n\n"
            f"Query: {query}\n\n"
            f"Opinions:\n{opinion_ctx}\n\n"
            f"Reviews:\n{review_ctx}\n\n"
            f"Provide a final, authoritative response."
        )

        chair_res = await ask_ollama_with_metrics(
            client,
            CHAIRMAN["url"],
            CHAIRMAN["model"],
            chair_prompt,
            "CHAIRMAN"
        )

        total_duration = time.time() - overall_start
        print(f"\n✨ SESSION COMPLETE in {total_duration:.2f}s")
        print("=" * 50 + "\n")

        return {
            "opinions": opinions,
            "reviews": reviews,
            "final": {"response": chair_res["response"], "latency": chair_res["latency"]},
            "total_time": f"{total_duration:.2f}s"
        }
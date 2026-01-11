# backend/council.py
import httpx
import asyncio
import time

from backend.config import (
    COUNCIL_MEMBERS,
    CHAIRMAN,
    REQUEST_TIMEOUT,
    MAX_HISTORY_MESSAGES
)
from backend.memory_manager import build_context, save_memory


async def call_ollama(url, model, prompt):
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return {
                "response": data.get("response", ""),
                "latency": round(time.time() - start, 2)
            }
    except Exception as e:
        return {
            "response": f"ERROR: {str(e)}",
            "latency": 0
        }


async def stage_one_opinions(query, context):
    tasks = {}
    for name, node in COUNCIL_MEMBERS.items():
        prompt = (
            f"{context}"
            f"User Question:\n{query}\n\n"
            "Provide your independent expert answer."
        )
        tasks[name] = call_ollama(node["url"], node["model"], prompt)

    results = await asyncio.gather(*tasks.values())
    return dict(zip(tasks.keys(), results))


async def stage_two_reviews(query, opinions):
    reviews = {}
    for reviewer, node in COUNCIL_MEMBERS.items():
        anonymized = []
        for name, content in opinions.items():
            if name != reviewer:
                anonymized.append(f"Response:\n{content['response'][:500]}")

        prompt = (
            f"User Question:\n{query}\n\n"
            "You are reviewing anonymous peer answers.\n"
            + "\n\n".join(anonymized)
            + "\n\nRate each response (1–10) based on accuracy and insight."
        )

        reviews[reviewer] = await call_ollama(
            node["url"], node["model"], prompt
        )

    return reviews


async def stage_three_chairman(query, context, opinions, reviews):
    compiled_opinions = "\n".join(
        f"{name}: {data['response'][:600]}"
        for name, data in opinions.items()
    )

    compiled_reviews = "\n".join(
        f"{name}: {data['response'][:300]}"
        for name, data in reviews.items()
    )

    prompt = (
        f"{context}"
        f"User Question:\n{query}\n\n"
        "Council Member Answers:\n"
        f"{compiled_opinions}\n\n"
        "Peer Reviews:\n"
        f"{compiled_reviews}\n\n"
        "As Chairman, synthesize a single authoritative final answer."
    )

    return await call_ollama(
        CHAIRMAN["url"],
        CHAIRMAN["model"],
        prompt
    )


async def run_council(query, history=None):
    context = build_context()

    if history:
        recent = history[-MAX_HISTORY_MESSAGES:]
        context += "RECENT CHAT HISTORY:\n"
        for msg in recent:
            context += f"{msg['role']}: {msg['content'][:200]}\n"
        context += "\n"

    opinions = await stage_one_opinions(query, context)
    reviews = await stage_two_reviews(query, opinions)
    final = await stage_three_chairman(query, context, opinions, reviews)

    save_memory(query, final["response"])

    return {
        "opinions": opinions,
        "reviews": reviews,
        "final": final
    }

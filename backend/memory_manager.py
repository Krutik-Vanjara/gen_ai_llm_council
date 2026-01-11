# backend/memory_manager.py
import json
import os

MEMORY_FILE = "council_memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(query, final_answer):
    memory = load_memory()
    memory.append({
        "query": query,
        "final_answer": final_answer
    })
    # Keep only last 5 interactions
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory[-5:], f, indent=2)

def build_context():
    history = load_memory()
    if not history:
        return ""

    context = "PAST DISCUSSION SUMMARY:\n"
    for item in history:
        context += f"- Q: {item['query']}\n"
        context += f"  A: {item['final_answer'][:200]}...\n"
    context += "\n"
    return context

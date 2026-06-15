"""End-to-end demo. Requires BRAVE_API_KEY in your environment."""
from bravelab import BraveSearchClient, TrendMonitor, answer_question

client = BraveSearchClient()

print("== Web search ==")
for r in client.web("brave search api", count=3):
    print("-", r.title, "->", r.url)

print("\n== Ask (web-grounded) ==")
print(answer_question("What is the Brave Search API?", client, top_k=4).render())

print("\n== Trend monitor ==")
for p in TrendMonitor(client).leaderboard(["openai", "anthropic", "mistral ai"]):
    print(f"{p.topic:<14} {p.temperature:<8} buzz={p.buzz_score}")

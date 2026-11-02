"""
GFC Financial Chatbot: simple Flask web interface.

Run from the project folder:
    python -m chatbot.app
Then open http://127.0.0.1:5000 in a browser.

Each browser session gets its own chatbot, so follow-up questions remember
that user's conversation (state management).
"""

from __future__ import annotations

import uuid

from flask import Flask, jsonify, render_template_string, request, session

from chatbot.financial_chatbot import FinancialChatbot

app = Flask(__name__)
app.secret_key = "gfc-prototype-only-change-in-production"

_bots: dict[str, FinancialChatbot] = {}


def _bot_for_session() -> FinancialChatbot:
    if "id" not in session:
        session["id"] = uuid.uuid4().hex
    return _bots.setdefault(session["id"], FinancialChatbot())


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GFC Financial Chatbot</title>
<style>
  :root { --brand: #1f4e3d; --bg: #f6f7f6; --bot: #ffffff; --user: #e3efe9; --text: #1d1d1d; --muted: #6b6b6b; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }
  header { background: var(--brand); color: #fff; padding: 16px 20px; }
  header h1 { margin: 0; font-size: 1.15rem; }
  header p { margin: 4px 0 0; font-size: 0.85rem; opacity: 0.85; }
  main { max-width: 760px; margin: 0 auto; padding: 16px; display: flex; flex-direction: column; height: calc(100vh - 74px); }
  #log { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-bottom: 8px; }
  .msg { padding: 10px 14px; border-radius: 12px; max-width: 92%; white-space: pre-wrap; line-height: 1.45; font-size: 0.95rem; }
  .bot { background: var(--bot); align-self: flex-start; border: 1px solid #e2e4e2; font-family: ui-monospace, Consolas, monospace; font-size: 0.85rem; }
  .user { background: var(--user); align-self: flex-end; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
  .chip { border: 1px solid var(--brand); color: var(--brand); background: #fff; border-radius: 16px; padding: 5px 10px; font-size: 0.8rem; cursor: pointer; }
  form { display: flex; gap: 8px; }
  input { flex: 1; padding: 12px; border: 1px solid #cfd3cf; border-radius: 10px; font-size: 1rem; }
  button[type=submit] { background: var(--brand); color: #fff; border: 0; border-radius: 10px; padding: 0 18px; font-size: 1rem; cursor: pointer; }
  footer { font-size: 0.75rem; color: var(--muted); margin-top: 8px; }
</style>
</head>
<body>
<header>
  <h1>GFC Financial Chatbot</h1>
  <p>Microsoft, Tesla and Apple | 10-K data, FY2023 to FY2025</p>
</header>
<main>
  <div id="log"><div class="msg bot">Hello! Ask me about revenue, profit, assets, liabilities, cash flow or margins for Microsoft, Tesla or Apple. Type 'help' for examples.</div></div>
  <div class="chips">
    <button class="chip">What was Apple's revenue in 2025?</button>
    <button class="chip">How has Tesla's net income changed over the last year?</button>
    <button class="chip">Which company has the highest net margin?</button>
    <button class="chip">Show a chart of revenue</button>
  </div>
  <form id="f"><input id="q" autocomplete="off" placeholder="Ask a question..." aria-label="Your question"><button type="submit">Send</button></form>
  <footer>Prototype. Figures from company 10-K filings. Not investment advice.</footer>
</main>
<script>
  const log = document.getElementById('log'), q = document.getElementById('q');
  function add(text, who) { const d = document.createElement('div'); d.className = 'msg ' + who; d.textContent = text; log.appendChild(d); log.scrollTop = log.scrollHeight; }
  async function ask(text) {
    if (!text.trim()) return;
    add(text, 'user'); q.value = '';
    const r = await fetch('/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text})});
    const data = await r.json(); add(data.reply, 'bot');
  }
  document.getElementById('f').addEventListener('submit', e => { e.preventDefault(); ask(q.value); });
  document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => ask(c.textContent)));
</script>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/chat")
def chat():
    message = (request.get_json(silent=True) or {}).get("message", "")
    return jsonify({"reply": _bot_for_session().respond(str(message)[:500])})


if __name__ == "__main__":
    app.run(debug=False)

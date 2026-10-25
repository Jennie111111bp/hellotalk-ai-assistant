import os
from flask import Flask, request, render_template_string, jsonify
from google import genai

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HelloTalk AI Assistant</title>
<style>
body {
    font-family: Arial, sans-serif;
    max-width: 600px;
    margin: 30px auto;
    padding: 16px;
    background: #f4f7fb;
}
main {
    background: white;
    padding: 20px;
    border-radius: 14px;
}
textarea, input, button {
    box-sizing: border-box;
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    font-size: 16px;
}
button {
    background: #2878e5;
    color: white;
    border: 0;
    border-radius: 8px;
}
#reply {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #eef5ff;
    padding: 12px;
    border-radius: 8px;
}
</style>
</head>
<body>
<main>
<h2>🌏 HelloTalk AI Reply Assistant</h2>
<p>Paste a message to generate a natural reply.</p>

<label>Partner's name (optional)</label>
<input id="name" placeholder="e.g. Mina">

<label>Incoming message</label>
<textarea id="message" rows="5"
placeholder="Paste their message here"></textarea>

<label>Reply style</label>
<select id="style" style="width:100%;padding:12px">
<option>Friendly and natural</option>
<option>Short and casual</option>
<option>Ask an interesting follow-up question</option>
<option>Help me practise the language</option>
</select>

<button onclick="generateReply()">Generate reply</button>
<p id="status"></p>
<div id="reply"></div>
<button onclick="copyReply()">Copy reply</button>
</main>

<script>
async function generateReply() {
    const message = document.getElementById("message").value.trim();
    const name = document.getElementById("name").value.trim();
    const style = document.getElementById("style").value;
    const status = document.getElementById("status");
    const reply = document.getElementById("reply");

    if (!message) {
        status.textContent = "Please paste a message first.";
        return;
    }

    status.textContent = "Generating your reply...";
    reply.textContent = "";

    try {
        const response = await fetch("/api/reply", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message, name, style})
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Request failed");

        reply.textContent = data.reply;
        status.textContent = "Reply ready!";
    } catch (error) {
        status.textContent = "Error: " + error.message;
    }
}

function copyReply() {
    const text = document.getElementById("reply").textContent;
    if (text) navigator.clipboard.writeText(text);
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/reply", methods=["POST"])
def generate_reply():
    if not client:
        return jsonify({"error": "GEMINI_API_KEY is not configured in Render."}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    name = str(data.get("name", "")).strip()[:80]
    style = str(data.get("style", "Friendly and natural"))[:100]

    if not message:
        return jsonify({"error": "Please provide a message."}), 400

    prompt = f"""
You are a helpful language-exchange reply assistant.
Understand the incoming message and identify its language.
Write one natural, friendly reply in the same language as the
incoming message, unless the message clearly requests another language.
Keep the reply concise, conversational, and appropriate for a
language-exchange conversation.
Follow this style: {style}
Partner name, if provided: {name or "Not provided"}
Incoming message:
{message}

Return only the reply text, without explanations or quotation marks.
"""

    try:
        result = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return jsonify({"reply": result.text or "No reply was generated."})
    except Exception:
        app.logger.exception("Gemini API request failed")
        return jsonify({
            "error": "Gemini request failed. Check the API key, model access, and usage limits in Render."
        }), 502

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

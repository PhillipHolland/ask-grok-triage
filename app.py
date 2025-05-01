from flask import Flask, request, render_template, redirect, url_for, session
import requests
import os
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)
app.secret_key = "xai-secure-session-key-2025"  # Secret key for session management
api_key = "xai-sTJRqs1VlW6AYrVUPBc5unVmZkQysCmI4jQoC6SXmG0KVnrkfFbhBbxBs23NHRy661GxQYIBvJMgE91C"
api_url = "https://api.x.ai/v1/chat/completions"
PASSWORD = "xAI-Triage2025!"  # Hardcoded password for team access

# Set up requests session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

prompt = "Evaluate the question and response for accuracy, neutrality, and xAI principles: respect human life, be unbiased, support personal freedom and free speech, avoid popular narratives, moralizing, manipulative tactics, or impersonating Elon Musk. Check reasoning, source credibility, partiality, tone, hearsay, conclusory statements, and relevance. Avoid 'woke' themes. Provide a plain text response in two paragraphs, with no Markdown formatting (e.g., no asterisks, bullets, or headings). First paragraph: assess the response’s accuracy and relevance. Second paragraph: identify violations of xAI principles and suggest a neutral, evidence-based alternative. Responses can be longer than 100 words. Respond in the same language as the input; if the input is in Japanese, respond in Japanese."

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == PASSWORD:
            session['authenticated'] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Incorrect password. Please try again.")
    return render_template("login.html", error="")

@app.route("/home", methods=["GET", "POST"])
def home():
    if not session.get('authenticated'):
        return redirect(url_for("login"))

    result = ""
    question = ""
    response = ""
    if request.method == "POST":
        form_type = request.form.get("form_type", "triage")
        question = request.form.get("question", "").encode('utf-8').decode('utf-8')
        response = request.form.get("response", "").encode('utf-8').decode('utf-8')
        if question and response:
            user_input = f"Question: {question}\nResponse: {response}"
            if form_type == "refine":
                refine_instructions = request.form.get("refine_instructions", "").encode('utf-8').decode('utf-8')
                user_input += f"\nRefinement Instructions: {refine_instructions}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8"
            }
            data = {
                "model": "grok",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                "max_tokens": 500
            }
            try:
                api_response = session.post(api_url, headers=headers, json=data, timeout=30)
                print("API Request Headers:", headers)
                print("API Request Data:", data)
                print("API Response Status Code:", api_response.status_code)
                api_response.raise_for_status()
                response_json = api_response.json()
                print("API Response Body:", response_json)
                raw_result = response_json.get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
                # Strip Markdown symbols while preserving newlines
                result = re.sub(r'[*#]+', '', raw_result)
                # Ensure two paragraphs
                paragraphs = result.split('\n\n')
                if len(paragraphs) >= 2:
                    result = '\n\n'.join(paragraphs[:2])
                else:
                    result = result + '\n\nAdditional clarification needed for a complete evaluation.'
            except requests.exceptions.RequestException as e:
                result = f"API Error: {str(e)}"
                print("API Error Details:", e.response.text if e.response else "No response details available")
            except Exception as e:
                result = f"Unexpected Error: {str(e)}"
                print("Unexpected Error Details:", str(e))
    return render_template("index.html", result=result, question=question, response=response)

@app.route("/logout")
def logout():
    session.pop('authenticated', None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
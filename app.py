from flask import Flask, request, render_template
import requests
import os
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)
api_key = "xai-sTJRqs1VlW6AYrVUPBc5unVmZkQysCmI4jQoC6SXmG0KVnrkfFbhBbxBs23NHRy661GxQYIBvJMgE91C"
api_url = "https://api.x.ai/v1/chat/completions"

# Set up requests session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

prompt = "Evaluate the question and response for accuracy, neutrality, and xAI principles: respect human life, be unbiased, support personal freedom and free speech, avoid popular narratives, moralizing, manipulative tactics, or impersonating Elon Musk. Check reasoning, source credibility, partiality, tone, hearsay, conclusory statements, and relevance. Avoid 'woke' themes. Provide a concise plain text response in two paragraphs, with no Markdown formatting (e.g., no asterisks, bullets, or headings). First paragraph: outline where the response failed. Second paragraph: provide an improved version with minimal explanation. Respond entirely in the same language as the input; if the input is in Japanese, respond fully in Japanese with no English mixed in, translating all terms, citations, references, and any other content into Japanese, even if originally in English. If refining a previous response, improve upon it based on the refinement instructions and triager notes without starting over."

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""
    question = ""
    response = ""
    triager_notes = ""
    previous_result = request.form.get("previous_result", "")
    if request.method == "POST":
        form_type = request.form.get("form_type", "triage")
        question = request.form.get("question", "").encode('utf-8').decode('utf-8')
        response = request.form.get("response", "").encode('utf-8').decode('utf-8')
        triager_notes = request.form.get("triager_notes", "").encode('utf-8').decode('utf-8')
        if question and response:
            user_input = f"Question: {question}\nResponse: {response}"
            if triager_notes:
                user_input += f"\nTriager Notes: {triager_notes}"
            if form_type == "refine":
                refine_instructions = request.form.get("refine_instructions", "").encode('utf-8').decode('utf-8')
                user_input += f"\nPrevious Result: {previous_result}\nRefinement Instructions: {refine_instructions}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8"
            }
            data = {
                "model": "grok-3",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                "max_tokens": 500,
                "stream": False,
                "temperature": 0
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
                    result = result + '\n\n完全な評価にはさらなる明確化が必要です。'
                # Check if the response contains English characters (a-z, A-Z) mixed with Japanese
                if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', user_input):
                    error = "応答は完全に日本語である必要があります。再度試してください。"
                    result = error
            except requests.exceptions.RequestException as e:
                error = "APIエラー: しばらくしてから再度お試しください。"
                result = "リクエスト処理中にエラーが発生しました。しばらくしてから再度お試しください。"
                print("API Error Details:", e.response.text if e.response else "No response details available")
            except Exception as e:
                error = "予期しないエラー: しばらくしてから再度お試しください。"
                result = "予期しないエラーが発生しました。しばらくしてから再度お試しください。"
                print("Unexpected Error Details:", str(e))
    return render_template("index.html", result=result, error=error, question=question, response=response, triager_notes=triager_notes, previous_result=result)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
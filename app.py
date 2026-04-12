from  flask import Flask, jsonify, request
from google import genai
import requests
from bs4 import BeautifulSoup
import os
import io
import pymupdf 

app = Flask(__name__)

# Configure Gemini API key
Client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))


# for model in genai.list_models():
#     print(model)

def extract_text_from_pdf(pdf_file):
    with pymupdf.open(stream=pdf_file, filetype="pdf") as doc:
        text = ""
        for  page in doc:
            text += page.get_text()
    return text

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        #remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        # Clean up  whitespace
        lines =  (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        return f"Error fetching URL: {e}"
    
def summarize_text(text, max_length=150):
    prompt = f"Summarize the following text in about {max_length} words or less: {text}"
    try:
        response = Client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"
    
@app.route("/api/pdf", methods=["POST"])
def summarize_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    try:
        pdf_text = extract_text_from_pdf(io.BytesIO(file.read()))
        summary = summarize_text(pdf_text)
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

app.route("/api/url", methods=['POST'])
def summarize_url():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "No url provided"}), 400
    try:
        text = extract_text_from_url(url)
        summary = summarize_text(text)
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

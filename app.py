from flask import Flask, jsonify, request, render_template_string
import openai
import requests
from bs4 import BeautifulSoup
import os
import io
import pymupdf 
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment")

app = Flask(__name__)


# for model in openai.Model.list():
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
    prompt = f"Summarize the following text in about {max_length} words or less:\n\n{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message["content"].strip()
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

@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Summarizer App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            width: 400px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 10px;
            color: #555;
        }
        select, input[type="file"], input[type="text"], input[type="submit"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        input[type="submit"] {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Summarizer App</h1>
        <form action="/summarize" method="post" enctype="multipart/form-data">
            <label for="option">Choose input type:</label>
            <select name="option" id="option">
                <option value="pdf">PDF</option>
                <option value="url">URL</option>
            </select><br><br>
            <div id="pdf_input">
                <label for="file">Choose PDF file:</label>
                <input type="file" name="file" accept=".pdf"><br><br>
            </div>
            <div id="url_input" style="display:none;">
                <label for="url">Enter URL:</label>
                <input type="text" name="url"><br><br>
            </div>
            <input type="submit" value="Summarize">
        </form>
    </div>
    <script>
        document.getElementById('option').addEventListener('change', function() {
            var option = this.value;
            if (option === 'pdf') {
                document.getElementById('pdf_input').style.display = 'block';
                document.getElementById('url_input').style.display = 'none';
            } else {
                document.getElementById('pdf_input').style.display = 'none';
                document.getElementById('url_input').style.display = 'block';
            }
        });
    </script>
</body>
</html>
""")

@app.route("/summarize", methods=["POST"])
def summarize():
    option = request.form.get('option')
    if option == 'pdf':
        if 'file' not in request.files:
            return "No file provided", 400
        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400
        try:
            pdf_text = extract_text_from_pdf(io.BytesIO(file.read()))
            summary = summarize_text(pdf_text)
            return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Summary</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            width: 600px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        p {
            color: #555;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        a {
            display: inline-block;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        a:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Summary</h1>
        <p>{{ summary }}</p>
        <a href="/">Back</a>
    </div>
</body>
</html>
""", summary=summary)
        except Exception as e:
            return f"Error: {str(e)}", 500
    elif option == 'url':
        url = request.form.get('url')
        if not url:
            return "No URL provided", 400
        try:
            text = extract_text_from_url(url)
            summary = summarize_text(text)
            return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Summary</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            width: 600px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        p {
            color: #555;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        a {
            display: inline-block;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        a:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Summary</h1>
        <p>{{ summary }}</p>
        <a href="/">Back</a>
    </div>
</body>
</html>
""", summary=summary)
        except Exception as e:
            return f"Error: {str(e)}", 500
    else:
        return "Invalid option", 400

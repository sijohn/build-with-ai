import json
import os
from flask import Flask, request, jsonify
# Removed PIL imports as image conversion is no longer needed
# import io
from dotenv import load_dotenv # Import load_dotenv

# --- Load environment variables from .env file at the very beginning ---
load_dotenv()
# -----------------------------------------------------------------------

# Now import your AI prediction module
from ai_predict import generate_v2, Invoice # Import the Invoice model too

app = Flask(__name__)

# Consider defining prompt externally or pass it to the function if it's dynamic
prompt = """
You are a document entity extraction specialist.
Given a document, your task is to extract the text value of entities.
- Generate null for missing entities.
"""

# Removed the convert_image_to_pdf function

@app.route('/process_file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Use file.mimetype which is more reliable than guessing from extension
    document_bytes = file.read()
    mime_type = file.mimetype

    # Check if a valid file type is provided based on mime type
    if mime_type in ['application/pdf', 'image/jpeg', 'image/png']:
        # Pass original bytes and correct mime type directly
        parsed_output = generate_v2(prompt, document_bytes, mime_type=mime_type)

        if parsed_output:
             # generate_v2 now returns the parsed Python object (Pydantic model instance)
             # jsonify can directly serialize Pydantic models or dictionaries
             return jsonify(parsed_output.model_dump()), 200 # Use .model_dump() for dict representation
        else:
             # Handle cases where generate_v2 didn't return a parsed object
             return jsonify({"error": "AI prediction failed or returned no parsed data"}), 500

    else:
        return jsonify({"error": f"Invalid file type: {mime_type}. Only PDF, JPG, and PNG are supported."}), 400

# Add a basic health check endpoint (optional but good practice)
@app.route('/health', methods=['GET'])
def health_check():
    # You could add logic here to check the connection to Vertex AI if needed
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    # The port is read from the environment variable PORT, defaulting to 8080
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask app on http://0.0.0.0:{port}")
    # Set debug=True for local development to see errors and auto-reload
    # Remember to turn off debug=True in production!
    app.run(host='0.0.0.0', port=port, debug=True)
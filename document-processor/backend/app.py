import json
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()
# -------------------------------------------------

# Import your AI prediction module and the BigQuery write function
from ai_predict import generate_v2, Invoice # Import write_to_bigquery
from bq_helper import write_to_bigquery # Import write_to_bigquery

app = Flask(__name__)

# Define BigQuery parameters - read from environment variables
# Add these to your .env file:
# BQ_DATASET_ID=your_bq_dataset
# BQ_TABLE_ID=your_bq_table
BQ_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") # Use the same project ID
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID")
BQ_TABLE_ID = os.environ.get("BQ_TABLE_ID")

# Basic check to ensure BQ variables are set
if not all([BQ_PROJECT_ID, BQ_DATASET_ID, BQ_TABLE_ID]):
    print("WARNING: BigQuery environment variables (GOOGLE_CLOUD_PROJECT, BQ_DATASET_ID, BQ_TABLE_ID) are not fully set.")
    print("BigQuery writing will be skipped.")
    # You might want to exit or raise an error in a real application
    BQ_WRITING_ENABLED = False
else:
    BQ_WRITING_ENABLED = True
    print(f"BigQuery writing enabled for {BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}")


prompt = """
You are a document entity extraction specialist.
Given a document, your task is to extract the text value of entities.
- Generate null for missing entities.
"""

@app.route('/process_file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    document_bytes = file.read()
    mime_type = file.mimetype

    if mime_type in ['application/pdf', 'image/jpeg', 'image/png']:
        parsed_output = generate_v2(prompt, document_bytes, mime_type=mime_type)

        if parsed_output:
            # --- Add this block to write to BigQuery ---
            if BQ_WRITING_ENABLED:
                write_to_bigquery(parsed_output, BQ_PROJECT_ID, BQ_DATASET_ID, BQ_TABLE_ID)
            else:
                 print("BigQuery writing is disabled due to missing configuration.")
            # -------------------------------------------

            # Return the JSON response as before
            return jsonify(parsed_output.model_dump()), 200
        else:
            return jsonify({"error": "AI prediction failed or returned no parsed data"}), 500

    else:
        return jsonify({"error": f"Invalid file type: {mime_type}. Only PDF, JPG, and PNG are supported."}), 400

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask app on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
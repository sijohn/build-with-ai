import traceback
from typing import List
from google import genai
from google.genai import types
from pydantic import BaseModel
import base64
import os
from dotenv import load_dotenv # Import load_dotenv

# --- Load environment variables from .env file (if this script is run directly) ---
# It's generally loaded in the main entry point (app.py), but harmless here.
load_dotenv()
# ---------------------------------------------------------------------------------

# Read from environment, providing a default if not set (e.g., from .env or system)
GCP_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") 
VERTEX_AI_LOCATION = os.environ.get("VERTEX_AI_LOCATION", "us-central1") # Also good practice to make location configurable

print(f"Using GCP Project: {GCP_PROJECT_ID}, Vertex AI Location: {VERTEX_AI_LOCATION}") # Added for debugging

# Define the Pydantic model for the items within the list
class InvoiceItem(BaseModel):
    description: str
    quantity: str
    total: str

# Update the Invoice model to include the items list
class Invoice(BaseModel):
    invoice_number: str | None = None # Added | None = None to make fields nullable as per typical model output
    supplier_name: str | None = None
    order_total: str | None = None
    items: List[InvoiceItem] | None = None # Lists might be null too

client = genai.Client(
      vertexai=True,
      project=GCP_PROJECT_ID,
      location=VERTEX_AI_LOCATION,
  )

def generate_v2(prompt,document_bytes, mime_type):
    # Add a check for supported mime types by the API if needed,
    # but the API typically handles common image/pdf types.
    print(f"Sending document with mime_type: {mime_type}") # Added for debugging

    image_parts = [
            types.Part.from_bytes(data=document_bytes, mime_type=mime_type)
        ]
    contents = [
        types.Content(role="user", parts=image_parts + [types.Part.from_text(text=prompt)])
    ]

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001', # Ensure this model supports vision/multimodal input
            contents=contents,
            config={
                'response_mime_type': 'application/json',
                'response_schema': Invoice, # Pass the Pydantic model directly
            },
        )
        print("Raw response text:", response.text)
        print("======================")

        # Check if the API returned a BlockedReason
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            print(f"API call blocked: {response.prompt_feedback.block_reason}")
            # You might want to raise an exception or return a specific error indicator
            return None # Indicate failure

        # Check for finish reason indicating issues
        if response.candidates:
             for candidate in response.candidates:
                 if candidate.finish_reason:
                     print(f"API call finished with reason: {candidate.finish_reason}")
                     if candidate.finish_reason != 'STOP': # 'STOP' is the normal successful reason
                          # Handle other finish reasons if necessary (e.g., MAX_TOKENS)
                          pass # Or log a warning/error


        if response.parsed:
            print("Parsed response:")
            # print(response.parsed) # Avoid printing large objects in logs
            # response.parsed should be the Invoice Pydantic model instance
            return response.parsed
        else:
            # This might happen if text is generated but doesn't match the schema
            print("response.parsed is None or empty, but response text might exist.")
            # Consider returning None or the raw text if schema parsing failed but text was generated
            return None
    except Exception as e:
        print(f"An error occurred during AI generation: {e}")
        traceback.print_exc() # Print detailed traceback
        return None # Indicate failure
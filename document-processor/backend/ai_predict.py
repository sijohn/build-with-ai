import traceback
from typing import List
from google import genai
from google.genai import types
from pydantic import BaseModel
import base64
import os


GCP_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") # Replace with your default project ID
VERTEX_AI_LOCATION = "us-central1" # Replace with your Vertex AI region

# Define the Pydantic model for the items within the list
class InvoiceItem(BaseModel):
    description: str
    quantity: str
    total: str

# Update the Invoice model to include the items list
class Invoice(BaseModel):
    invoice_number: str
    supplier_name: str
    order_total: str
    items: List[InvoiceItem]

client = genai.Client(
      vertexai=True,
      project=GCP_PROJECT_ID,
      location=VERTEX_AI_LOCATION,
  )

def generate_v2(prompt,document_bytes, mime_type):
    # Generate a list of cookie recipes
    image_parts = [
            types.Part.from_bytes(data=document_bytes, mime_type=mime_type)
        ]
    contents = [
        types.Content(role="user", parts=image_parts + [types.Part.from_text(text=prompt)])
    ]

    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=contents,
        config={
            'response_mime_type': 'application/json',
            'response_schema': Invoice,
        },
    )
    print(response.text)
    print("======================")
    if response.parsed:
        # Print the parsed response
        print("Parsed response:")
        print(response.parsed)
       
        return response.parsed
    else:
        print("response.parsed is None or empty.")
        return None
    


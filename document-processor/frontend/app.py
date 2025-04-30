import streamlit as st
import requests
import base64
from PIL import Image
import pandas as pd # Import pandas to create DataFrames

# Define the API endpoint for document extraction
# Make sure this endpoint is correct and accessible
API_ENDPOINT = "https://document-processing-be-sqtgj6feba-lz.a.run.app/process_file"

# Function to extract text from PDF or image using the extraction API
def extract_data(file, mime_type):
    # Reset file pointer to the beginning before sending
    file.seek(0)
    # Prepare files dictionary for requests.post
    # The key 'file' must match the name expected by your Flask backend (request.files['file'])
    files = {'file': (file.name, file, mime_type)}
    try:
        response = requests.post(API_ENDPOINT, files=files)
        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()
        # Return the JSON response as a Python dictionary
        return response.json()
    except requests.exceptions.RequestException as e:
        # Catch any request-related errors (connection, HTTP errors, etc.)
        st.error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError:
        # Handle cases where the response is not valid JSON
        st.error("API returned a non-JSON response.")
        return None


# Function to display PDF in Streamlit using an iframe
def display_pdf(file, height=500): # Increased default height slightly
    # Reset file pointer for reading
    file.seek(0)
    try:
        # Read file content, encode to base64, and decode to utf-8 string
        base64_pdf = base64.b64encode(file.read()).decode('utf-8')
        # Create an HTML iframe to embed the base64 encoded PDF
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}px" style="border: none;"></iframe>'
        # Render the iframe using st.markdown with unsafe_allow_html
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not display PDF: {e}")


# Function to display an image in Streamlit
def display_image(file):
    try:
        # Open the image file using Pillow
        image = Image.open(file)
        # Display the image in Streamlit, adjusting width to column
        st.image(image, use_column_width=True)
    except Exception as e:
        st.error(f"Could not display image: {e}")


# Streamlit UI setup
st.set_page_config(layout="wide", page_title="Document Extraction Demo") # Added page title
st.title("Document Extraction with AI")
st.write("Upload a PDF or Image file to extract structured information using a custom API.")

# Create a two-column layout for file upload/results and document preview
col1, col2 = st.columns([1, 2]) # Adjust column ratio if needed

with col1:
    st.header("Upload Document")
    # File uploader widget for PDF and image files
    uploaded_file = st.file_uploader("Choose a PDF or Image file", type=["pdf", "png", "jpg", "jpeg"])

    # Button to trigger extraction
    if uploaded_file is not None:
        # Determine mime type based on the uploaded file's type attribute
        mime_type = uploaded_file.type
        # Basic validation for supported types before calling API
        if mime_type not in ["application/pdf", "image/png", "image/jpeg"]:
             st.warning(f"Unsupported file type: {mime_type}. Please upload PDF, PNG, or JPG.")
             extracted_data = None # Ensure no extraction attempt for unsupported types
        else:
            if st.button("Extract Information"):
                with st.spinner(f"Extracting information from {uploaded_file.name}..."):
                    # Call the extraction function
                    extracted_data = extract_data(uploaded_file, mime_type)

                # --- Display Extracted Information ---
                if extracted_data:
                    st.success("Information extracted successfully!")
                    st.write("## Extracted Information")

                    # Display main invoice details
                    st.subheader("Invoice Details")
                    # Create a dictionary for main details, handling potential missing keys gracefully
                    main_details = {
                        "Invoice Number": extracted_data.get("invoice_number", "N/A"),
                        "Supplier Name": extracted_data.get("supplier_name", "N/A"),
                        "Order Total": extracted_data.get("order_total", "N/A")
                    }
                    # Display main details as key-value pairs
                    for key, value in main_details.items():
                        st.write(f"**{key}:** {value}")

                    # Display items as a table
                    st.subheader("Items")
                    # Get the items list, default to empty list if not present or None
                    items_list = extracted_data.get("items", [])
                    if items_list:
                        try:
                            # Convert list of dictionaries to pandas DataFrame
                            items_df = pd.DataFrame(items_list)
                            # Display the DataFrame as a table
                            st.dataframe(items_df, use_container_width=True)
                        except Exception as e:
                            st.error(f"Could not display items as a table: {e}")
                            # Fallback to displaying raw items list if table conversion fails
                            st.write("Raw items data:")
                            st.json(items_list)
                    else:
                        st.info("No items extracted.")

                # No need for st.json(extracted_data) here anymore as we display structured data
    else:
        # Clear previous results when no file is uploaded
        extracted_data = None


with col2:
    st.header("Document Preview")
    # Display the uploaded file preview
    if uploaded_file is not None:
        # Reset file pointer for preview display
        uploaded_file.seek(0)
        if uploaded_file.type == "application/pdf":
            display_pdf(uploaded_file)
        else:
            display_image(uploaded_file)
    else:
        st.info("Upload a document in the left column to see a preview.")

# Optional: Add a footer
st.markdown("---")
st.markdown("Demo application for document extraction.")

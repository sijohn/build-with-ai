# Add this import at the top of ai_predict.py
import pandas as pd
import pandas_gbq
from ai_predict import Invoice

def write_to_bigquery(invoice_data: Invoice, project_id: str, dataset_id: str, table_id: str):
    """
    Writes parsed Invoice data to a Google BigQuery table.

    Args:
        invoice_data: The parsed Invoice Pydantic model instance.
        project_id: Your Google Cloud Project ID.
        dataset_id: The BigQuery Dataset ID.
        table_id: The BigQuery Table ID.
    """
    if not invoice_data:
        print("No invoice data to write to BigQuery.")
        return

    # Convert the Pydantic model to a dictionary
    # Use .model_dump() to get a dictionary representation, including nested models
    invoice_dict = invoice_data.model_dump()

    # pandas_gbq works well with a list of dictionaries.
    # We'll create a list containing just one dictionary for this single invoice.
    data_for_df = [invoice_dict]

    # Create a pandas DataFrame
    df = pd.DataFrame(data_for_df)

    # --- Handle the 'items' column for BigQuery STRUCT/ARRAY ---
    # pandas_gbq can automatically detect list of dicts and map to ARRAY<STRUCT>
    # if the schema is not explicitly provided and auto-detection is enabled.
    # However, sometimes explicitly converting list of Pydantic models to list of dicts is safer.
    # Since model_dump() already handles this, the default behavior should work.
    # If you encounter issues, you might need to manually ensure the 'items' column
    # contains lists of dictionaries:
    # df['items'] = df['items'].apply(lambda x: [item.model_dump() for item in x] if x else None)
    # But model_dump() on the main object should handle this correctly.

    # Define the full table path
    table_full_path = f"{project_id}.{dataset_id}.{table_id}"

    print(f"Attempting to write data to BigQuery table: {table_full_path}")

    try:
        # Use pandas_gbq.to_gbq to write the DataFrame
        # if_exists='append': Appends data if table exists, creates if not.
        # progress_bar=True: Shows a progress bar (useful for larger data, optional here)
        pandas_gbq.to_gbq(
            df,
            table_full_path,
            project_id=project_id,
            if_exists='append',
            progress_bar=False # Keep False for cleaner console output in a web demo
        )
        print("Data successfully written to BigQuery.")

    except Exception as e:
        print(f"An error occurred while writing to BigQuery: {e}")
        # You might want to log the error or handle it differently in a production app


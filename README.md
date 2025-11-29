# Bajaj Health Datathon - Bill Extraction API

This repository contains the solution for the Bajaj Health Datathon Bill Extraction problem. It provides an API to extract line item details and totals from bill/invoice documents.

## Approach
The solution uses a two-step process:
1.  **OCR (Optical Character Recognition)**: Extracts raw text from images and PDFs using Tesseract.
2.  **LLM (Large Language Model)**: Uses Google Gemini 1.5 Pro to analyze the text and extract structured data (line items, amounts, rates, quantities).

### Key Features
- **Accurate Extraction**: detailed prompt engineering to extract only monetary line items.
- **Total Reconciliation**:
    - Extracts "Page Total" and "Subtotal" to verify against the sum of line items.
    - Uses a **Regex Fallback** mechanism to find totals if the LLM fails to identify them.
    - Logs warnings if there is a mismatch between the calculated sum and the detected total.
- **Deduplication**: Logic to prevent double-counting of items (implemented in `utils.py`).
- **Robustness**: Handles multi-page PDFs and various image formats.

## Setup Instructions

### Prerequisites
- Python 3.9+
- Tesseract OCR (`sudo apt-get install tesseract-ocr`)
- Poppler (`sudo apt-get install poppler-utils`) for PDF processing

### Installation
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file with your API keys:
    ```
    GOOGLE_GEMINI_API_KEY=your_api_key_here
    # Optional:
    # LOG_LEVEL=INFO
    # HOST=0.0.0.0
    # PORT=3000
    ```

### Running the API
```bash
python -m app.main
# OR
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## API Documentation

### `POST /extract-bill-data`
Extracts data from a document URL.

**Request Body:**
```json
{
  "document": "https://example.com/bill.pdf"
}
```

**Response:**
```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 1500,
    "input_tokens": 1000,
    "output_tokens": 500
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Consultation Fee",
            "item_amount": 500.0,
            "item_rate": 500.0,
            "item_quantity": 1.0
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}
```

## Evaluation & Accuracy
The solution attempts to maximize accuracy by:
1.  Filtering out non-monetary items (dates, IDs).
2.  Explicitly asking the LLM to identify totals for verification.
3.  Using regex to double-check totals.
4.  Comparing `Sum(items)` vs `Detected Total` and logging discrepancies.

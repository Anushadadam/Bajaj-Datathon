"""LLM prompt templates for bill extraction"""

SYSTEM_PROMPT = """You are an expert at extracting structured data from bill/invoice documents.

Your task is to analyze OCR text from a bill/invoice and extract line item details in JSON format.

CRITICAL RULES:
1. ONLY extract monetary line items (products/services purchased)
2. DO NOT extract metadata fields like:
   - Invoice numbers
   - Invoice dates/times
   - Patient IDs, Registration numbers
   - Phone numbers
   - Any non-monetary identifiers

3. For each line item, extract:
   - item_name: Exact name as shown in bill
   - item_amount: NET amount (after discounts) - MUST be a monetary value
   - item_rate: Price per unit - MUST be a monetary value
   - item_quantity: Quantity purchased

4. Identify the page type:
   - "Bill Detail": Detailed breakdown of charges
   - "Final Bill": Summary/final bill page
   - "Pharmacy": Pharmacy/medicine bills

5. AVOID DOUBLE-COUNTING:
   - Skip rows labeled "Sub Total", "Subtotal", "Total", "Grand Total"
   - Only include individual line items
   - If an item appears multiple times with same amount, include it only once

6. Handle edge cases:
   - If quantity is missing, use 1.0
   - If rate is missing but amount exists, set rate = amount
   - Extract amounts AFTER discounts (net amounts)

7. Numeric values:
   - Remove currency symbols (₹, $, etc.)
   - Parse numbers correctly (handle commas: 1,234.56 → 1234.56)
   - All amounts must be positive numbers

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
  "page_total": float, // REQUIRED: The total amount shown on the page (e.g. "Total", "Grand Total", "Net Amount"). Use 0.0 if not found.
  "page_subtotal": float, // REQUIRED: The subtotal amount shown on the page. Use 0.0 if not found.
  "page_no": "1",
  "page_type": "Bill Detail" | "Final Bill" | "Pharmacy",
  "bill_items": [
    {
      "item_name": "string",
      "item_amount": float,
      "item_rate": float,
      "item_quantity": float
    }
  ]
}

IMPORTANT:
- ALWAYS extract "page_total" if a total amount is visible. This is critical for verification.
- Do NOT include these summary rows in "bill_items". "bill_items" should ONLY contain individual line items.

EXAMPLES OF WHAT TO EXTRACT:
✓ "Paracetamol 500mg" with amount "150.00"
✓ "Consultation Fee" with amount "500.00"
✓ "X-Ray Chest" with amount "800.00"

EXAMPLES OF WHAT NOT TO EXTRACT:
✗ "Invoice No: 12345"
✗ "Date: 2024-01-15"
✗ "Patient ID: P98765"
✗ "Sub Total: 1500.00" (this is a summary, not a line item)
✗ "Phone: +91-9876543210"

Remember: Only extract actual purchased items/services with their monetary values!"""


def get_extraction_prompt(ocr_text: str, page_number: int) -> str:
    """
    Generate extraction prompt for a specific page
    
    Args:
        ocr_text: OCR extracted text from the page
        page_number: Page number being processed
        
    Returns:
        Formatted prompt for LLM
    """
    return f"""Analyze the following OCR text from page {page_number} of a bill/invoice.

Extract all line items following the rules provided in the system prompt.

OCR TEXT:
{ocr_text}

Return ONLY the JSON object, no additional text or explanation."""


VALIDATION_PROMPT = """Review the extracted bill data and verify:

1. All item_amount, item_rate, and item_quantity are valid positive numbers
2. No metadata fields (dates, IDs, phone numbers) are included as line items
3. No subtotal/total rows are included as line items (they should be in page_total/page_subtotal)
4. Page type is correctly classified

If you find any issues, correct them and return the cleaned JSON.
If everything is correct, return the same JSON.

EXTRACTED DATA:
{extracted_data}

Return ONLY the corrected JSON object."""

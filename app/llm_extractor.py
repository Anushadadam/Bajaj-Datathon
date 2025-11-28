"""LLM-based extraction module using Google Gemini"""
import json
import logging
import re
from typing import List, Dict, Any, Tuple
import google.generativeai as genai

from app.config import settings
from app.prompts import SYSTEM_PROMPT, get_extraction_prompt
from app.models import BillItem, PagewiseLineItems

# Configure logging
logger = logging.getLogger(__name__)


class LLMExtractor:
    """Handles LLM-based structured data extraction from OCR text"""
    
    def __init__(self):
        """Initialize LLM extractor"""
        if not settings.google_gemini_api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY is required")
        
        # Configure Gemini
        genai.configure(api_key=settings.google_gemini_api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )
        
        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def extract_from_page(self, ocr_text: str, page_number: int) -> Dict[str, Any]:
        """
        Extract structured data from a single page's OCR text
        
        Args:
            ocr_text: OCR extracted text
            page_number: Page number
            
        Returns:
            Dictionary with extracted data
        """
        try:
            # Prepare prompt
            user_prompt = get_extraction_prompt(ocr_text, page_number)
            
            # Create chat with system instruction
            chat = self.model.start_chat(history=[])
            
            # Send message with system prompt context
            full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
            response = chat.send_message(full_prompt)
            
            # Track tokens
            if hasattr(response, 'usage_metadata'):
                self.total_input_tokens += response.usage_metadata.prompt_token_count
                self.total_output_tokens += response.usage_metadata.candidates_token_count
            
            # Parse response
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            json_text = self._extract_json(response_text)
            
            # Parse JSON
            extracted_data = json.loads(json_text)
            
            # Validate and clean data
            cleaned_data = self._validate_and_clean(extracted_data, page_number)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"LLM extraction failed for page {page_number}: {e}")
            # Return empty structure on error
            return {
                "page_no": str(page_number),
                "page_type": "Bill Detail",
                "bill_items": []
            }
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text (handle markdown code blocks)"""
        # Try to find JSON in markdown code block
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            return match.group(1)
        
        # Try to find raw JSON
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            return match.group(0)
        
        # Return as-is if no pattern found
        return text
    
    def _validate_and_clean(self, data: Dict[str, Any], page_number: int) -> Dict[str, Any]:
        """
        Validate and clean extracted data
        
        Args:
            data: Extracted data dictionary
            page_number: Page number
            
        Returns:
            Cleaned data dictionary
        """
        # Ensure required fields
        if 'page_no' not in data:
            data['page_no'] = str(page_number)
        
        if 'page_type' not in data:
            data['page_type'] = "Bill Detail"
        
        # Validate page_type
        valid_page_types = ["Bill Detail", "Final Bill", "Pharmacy"]
        if data['page_type'] not in valid_page_types:
            data['page_type'] = "Bill Detail"
        
        if 'bill_items' not in data:
            data['bill_items'] = []
        
        # Clean and validate bill items
        cleaned_items = []
        for item in data['bill_items']:
            cleaned_item = self._clean_bill_item(item)
            if cleaned_item:
                cleaned_items.append(cleaned_item)
        
        data['bill_items'] = cleaned_items
        
        return data
    
    def _clean_bill_item(self, item: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Clean and validate a single bill item
        
        Args:
            item: Item dictionary
            
        Returns:
            Cleaned item or None if invalid
        """
        try:
            # Extract fields
            item_name = str(item.get('item_name', '')).strip()
            
            # Skip if name is empty
            if not item_name:
                return None
            
            # Skip subtotal items
            if self._is_subtotal(item_name):
                logger.info(f"Skipping subtotal item: {item_name}")
                return None
            
            # Parse numeric fields
            item_amount = self._parse_number(item.get('item_amount', 0))
            item_rate = self._parse_number(item.get('item_rate', 0))
            item_quantity = self._parse_number(item.get('item_quantity', 1))
            
            # Validate amounts are positive
            if item_amount <= 0:
                logger.warning(f"Invalid amount for item '{item_name}': {item_amount}")
                return None
            
            # If rate is 0 but amount exists, set rate = amount
            if item_rate <= 0 and item_amount > 0:
                item_rate = item_amount
            
            # If quantity is 0, set to 1
            if item_quantity <= 0:
                item_quantity = 1.0
            
            return {
                'item_name': item_name,
                'item_amount': round(item_amount, 2),
                'item_rate': round(item_rate, 2),
                'item_quantity': round(item_quantity, 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to clean item: {e}")
            return None
    
    def _parse_number(self, value: Any) -> float:
        """Parse a number from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[₹$€£,\s]', '', value)
            
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _is_subtotal(self, item_name: str) -> bool:
        """Check if item name indicates a subtotal/summary row"""
        subtotal_patterns = [
            r'\bsub[\s\-]?total\b',
            r'\bgrand\s+total\b',
            r'\btotal\b',
            r'\bsummary\b',
            r'\bnet\s+amount\b',
            r'\bfinal\s+amount\b',
            r'\bamount\s+payable\b',
            r'\bbalance\b',
        ]
        
        item_name_lower = item_name.lower().strip()
        
        for pattern in subtotal_patterns:
            if re.search(pattern, item_name_lower):
                return True
        
        return False
    
    def extract_from_document(
        self, 
        page_texts: List[Tuple[int, str]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Extract data from all pages of a document
        
        Args:
            page_texts: List of (page_number, ocr_text) tuples
            
        Returns:
            Tuple of (extracted_pages, token_usage)
        """
        # Reset token counters
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        extracted_pages = []
        
        for page_num, ocr_text in page_texts:
            logger.info(f"Processing page {page_num}")
            
            # Skip empty pages
            if not ocr_text.strip():
                logger.warning(f"Page {page_num} has no text, skipping")
                continue
            
            # Extract data from page
            page_data = self.extract_from_page(ocr_text, page_num)
            
            # Only add pages with items
            if page_data.get('bill_items'):
                extracted_pages.append(page_data)
        
        # Calculate token usage
        token_usage = {
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens
        }
        
        return extracted_pages, token_usage
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get current token usage"""
        return {
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens
        }

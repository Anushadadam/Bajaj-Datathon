"""Utility functions for the Bill Extraction API"""
import os
import re
import tempfile
from typing import Tuple, List, Dict, Any
from urllib.parse import urlparse
import requests
from app.models import BillItem


def validate_document_url(url: str) -> bool:
    """Validate if the URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def download_document(url: str) -> Tuple[str, str]:
    """
    Download document from URL and save to temp file
    
    Args:
        url: Document URL
        
    Returns:
        Tuple of (file_path, file_extension)
        
    Raises:
        Exception: If download fails
    """
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Determine file extension from URL or content-type
        file_ext = detect_file_extension(url, response.headers.get('content-type', ''))
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        
        # Write content
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        
        temp_file.close()
        return temp_file.name, file_ext
        
    except Exception as e:
        raise Exception(f"Failed to download document: {str(e)}")


def detect_file_extension(url: str, content_type: str) -> str:
    """Detect file extension from URL or content type"""
    # Try to get from URL
    url_path = urlparse(url).path
    if '.' in url_path:
        ext = os.path.splitext(url_path)[1].lower()
        if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return ext
    
    # Try to get from content type
    content_type_map = {
        'application/pdf': '.pdf',
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/tiff': '.tiff',
        'image/bmp': '.bmp',
    }
    
    for ct, ext in content_type_map.items():
        if ct in content_type.lower():
            return ext
    
    # Default to .pdf
    return '.pdf'


def is_pdf(file_path: str) -> bool:
    """Check if file is a PDF"""
    return file_path.lower().endswith('.pdf')


def is_image(file_path: str) -> bool:
    """Check if file is an image"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    return any(file_path.lower().endswith(ext) for ext in image_extensions)


def calculate_total_amount(items: List[BillItem]) -> float:
    """Calculate total amount from bill items"""
    return sum(item.item_amount for item in items)


def is_subtotal_item(item_name: str) -> bool:
    """
    Detect if an item is a subtotal/summary row
    
    Common patterns:
    - "Sub Total", "Subtotal", "Sub-Total"
    - "Total", "Grand Total"
    - "Summary"
    """
    subtotal_patterns = [
        r'\bsub[\s\-]?total\b',
        r'\bgrand\s+total\b',
        r'\btotal\b',
        r'\bsummary\b',
        r'\bnet\s+amount\b',
        r'\bfinal\s+amount\b',
    ]
    
    item_name_lower = item_name.lower().strip()
    
    for pattern in subtotal_patterns:
        if re.search(pattern, item_name_lower):
            return True
    
    return False


def deduplicate_items(all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate items based on item_name and item_amount
    
    Args:
        all_items: List of item dictionaries
        
    Returns:
        Deduplicated list of items
    """
    seen = set()
    unique_items = []
    
    for item in all_items:
        # Create a unique key based on name and amount
        key = (item['item_name'].strip().lower(), item['item_amount'])
        
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    
    return unique_items


def extract_total_from_text(text: str) -> float:
    """
    Extract total amount from text using regex
    
    Args:
        text: OCR text
        
    Returns:
        Extracted total amount or 0.0
    """
    # Patterns for total amount
    # Look for "Total", "Net Amount", "Grand Total" followed by a number
    patterns = [
        r'(?:grand\s+)?total[\s:]+([₹$€£]?\s*[\d,]+\.?\d*)',
        r'net\s+amount[\s:]+([₹$€£]?\s*[\d,]+\.?\d*)',
        r'amount\s+payable[\s:]+([₹$€£]?\s*[\d,]+\.?\d*)',
        r'final\s+amount[\s:]+([₹$€£]?\s*[\d,]+\.?\d*)',
        r'balance\s+due[\s:]+([₹$€£]?\s*[\d,]+\.?\d*)'
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            # Get the last match as it's usually the final total
            amount_str = matches[-1]
            # Clean and parse
            cleaned = re.sub(r'[₹$€£,\s]', '', amount_str)
            try:
                return float(cleaned)
            except ValueError:
                continue
                
    return 0.0


def cleanup_temp_file(file_path: str):
    """Remove temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors

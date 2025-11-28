"""Unit tests for utility functions"""
import pytest
from app.utils import (
    validate_document_url,
    detect_file_extension,
    is_pdf,
    is_image,
    is_subtotal_item,
    calculate_total_amount,
    deduplicate_items
)
from app.models import BillItem


class TestURLValidation:
    """Test URL validation functions"""
    
    def test_valid_urls(self):
        assert validate_document_url("https://example.com/bill.pdf") == True
        assert validate_document_url("http://example.com/image.png") == True
    
    def test_invalid_urls(self):
        assert validate_document_url("not-a-url") == False
        assert validate_document_url("") == False
        assert validate_document_url("ftp://example.com") == True  # Valid URL format


class TestFileTypeDetection:
    """Test file type detection"""
    
    def test_pdf_detection(self):
        assert is_pdf("document.pdf") == True
        assert is_pdf("document.PDF") == True
        assert is_pdf("document.png") == False
    
    def test_image_detection(self):
        assert is_image("image.png") == True
        assert is_image("image.jpg") == True
        assert is_image("image.jpeg") == True
        assert is_image("document.pdf") == False
    
    def test_extension_detection(self):
        assert detect_file_extension("http://example.com/file.pdf", "") == ".pdf"
        assert detect_file_extension("http://example.com/file.png", "") == ".png"
        assert detect_file_extension("http://example.com/file", "application/pdf") == ".pdf"


class TestSubtotalDetection:
    """Test subtotal detection"""
    
    def test_subtotal_patterns(self):
        assert is_subtotal_item("Sub Total") == True
        assert is_subtotal_item("Subtotal") == True
        assert is_subtotal_item("Grand Total") == True
        assert is_subtotal_item("Total") == True
        assert is_subtotal_item("Net Amount") == True
    
    def test_non_subtotal_items(self):
        assert is_subtotal_item("Paracetamol") == False
        assert is_subtotal_item("Consultation Fee") == False
        assert is_subtotal_item("X-Ray") == False


class TestAmountCalculation:
    """Test amount calculation"""
    
    def test_calculate_total(self):
        items = [
            BillItem(item_name="Item 1", item_amount=100.0, item_rate=100.0, item_quantity=1.0),
            BillItem(item_name="Item 2", item_amount=200.0, item_rate=200.0, item_quantity=1.0),
            BillItem(item_name="Item 3", item_amount=50.5, item_rate=50.5, item_quantity=1.0),
        ]
        
        total = calculate_total_amount(items)
        assert total == 350.5


class TestDeduplication:
    """Test item deduplication"""
    
    def test_deduplicate_items(self):
        items = [
            {"item_name": "Item A", "item_amount": 100.0, "item_rate": 100.0, "item_quantity": 1.0},
            {"item_name": "Item B", "item_amount": 200.0, "item_rate": 200.0, "item_quantity": 1.0},
            {"item_name": "Item A", "item_amount": 100.0, "item_rate": 100.0, "item_quantity": 1.0},  # Duplicate
        ]
        
        unique = deduplicate_items(items)
        assert len(unique) == 2
        assert unique[0]["item_name"] == "Item A"
        assert unique[1]["item_name"] == "Item B"

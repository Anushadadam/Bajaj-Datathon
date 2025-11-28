"""OCR processing module for extracting text from images and PDFs"""
import os
import logging
from typing import List, Tuple
from PIL import Image
import pytesseract

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Google Cloud Vision (optional)
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    logger.warning("Google Cloud Vision not available, will use Tesseract")

# Try to import pdf2image (optional)
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available, PDF processing may fail")


class OCRProcessor:
    """Handles OCR extraction from images and PDFs"""
    
    def __init__(self):
        """Initialize OCR processor"""
        self.use_google_vision = (
            settings.use_google_vision and 
            GOOGLE_VISION_AVAILABLE and 
            settings.google_cloud_vision_api_key
        )
        
        if self.use_google_vision:
            logger.info("Using Google Cloud Vision API for OCR")
            self.vision_client = self._init_vision_client()
        else:
            logger.info("Using Tesseract for OCR")
            # Configure Tesseract path
            if settings.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
    
    def _init_vision_client(self):
        """Initialize Google Cloud Vision client"""
        try:
            # For API key authentication, we'll use it directly in requests
            # Google Cloud Vision Python client expects service account JSON
            # We'll implement a simpler approach using the REST API
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Vision client: {e}")
            return None
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from an image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        try:
            if self.use_google_vision and settings.google_cloud_vision_api_key:
                return self._extract_with_google_vision(image_path)
            else:
                return self._extract_with_tesseract(image_path)
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    def _extract_with_google_vision(self, image_path: str) -> str:
        """Extract text using Google Cloud Vision API"""
        try:
            import requests
            import base64
            
            # Read image and encode to base64
            with open(image_path, 'rb') as image_file:
                image_content = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare API request
            url = f"https://vision.googleapis.com/v1/images:annotate?key={settings.google_cloud_vision_api_key}"
            
            payload = {
                "requests": [
                    {
                        "image": {"content": image_content},
                        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                    }
                ]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract text from response
            if 'responses' in result and len(result['responses']) > 0:
                response_data = result['responses'][0]
                if 'fullTextAnnotation' in response_data:
                    return response_data['fullTextAnnotation']['text']
                elif 'textAnnotations' in response_data and len(response_data['textAnnotations']) > 0:
                    return response_data['textAnnotations'][0]['description']
            
            return ""
            
        except Exception as e:
            logger.warning(f"Google Vision failed, falling back to Tesseract: {e}")
            return self._extract_with_tesseract(image_path)
    
    def _extract_with_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Tesseract OCR failed: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Tuple[int, str]]:
        """
        Extract text from PDF file (page by page)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of tuples (page_number, extracted_text)
        """
        if not PDF2IMAGE_AVAILABLE:
            raise Exception("pdf2image is not installed. Cannot process PDF files.")
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300)
            
            results = []
            for page_num, image in enumerate(images, start=1):
                # Save image temporarily
                temp_image_path = f"/tmp/page_{page_num}.png"
                image.save(temp_image_path, 'PNG')
                
                # Extract text from image
                text = self.extract_text_from_image(temp_image_path)
                results.append((page_num, text))
                
                # Clean up temp file
                try:
                    os.unlink(temp_image_path)
                except:
                    pass
            
            return results
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def process_document(self, file_path: str, is_pdf: bool = False) -> List[Tuple[int, str]]:
        """
        Process document and extract text
        
        Args:
            file_path: Path to document
            is_pdf: Whether the document is a PDF
            
        Returns:
            List of tuples (page_number, extracted_text)
        """
        if is_pdf:
            return self.extract_text_from_pdf(file_path)
        else:
            text = self.extract_text_from_image(file_path)
            return [(1, text)]

"""FastAPI application for Bill Extraction API"""
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import (
    BillExtractionRequest,
    BillExtractionResponse,
    BillExtractionData,
    PagewiseLineItems,
    BillItem,
    TokenUsage,
    ErrorResponse
)
from app.utils import (
    validate_document_url,
    download_document,
    is_pdf,
    cleanup_temp_file,
    deduplicate_items
)
from app.ocr_processor import OCRProcessor
from app.llm_extractor import LLMExtractor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bill Extraction API",
    description="Extract line item details from bill/invoice documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
ocr_processor = OCRProcessor()
llm_extractor = LLMExtractor()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Bill Extraction API",
        "version": "1.0.0"
    }


@app.post("/extract-bill-data", response_model=BillExtractionResponse)
async def extract_bill_data(request: BillExtractionRequest):
    """
    Extract bill data from document URL
    
    Args:
        request: BillExtractionRequest with document URL
        
    Returns:
        BillExtractionResponse with extracted data
    """
    temp_file_path = None
    
    try:
        # Validate URL
        if not validate_document_url(request.document):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document URL"
            )
        
        logger.info(f"Processing document: {request.document}")
        
        # Download document
        try:
            temp_file_path, file_ext = download_document(request.document)
            logger.info(f"Downloaded document: {temp_file_path} ({file_ext})")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to download document: {str(e)}"
            )
        
        # Extract text using OCR
        try:
            is_pdf_file = is_pdf(temp_file_path)
            page_texts = ocr_processor.process_document(temp_file_path, is_pdf=is_pdf_file)
            logger.info(f"Extracted text from {len(page_texts)} pages")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {str(e)}"
            )
        
        # Extract structured data using LLM
        try:
            extracted_pages, token_usage = llm_extractor.extract_from_document(page_texts)
            logger.info(f"Extracted data from {len(extracted_pages)} pages")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM extraction failed: {str(e)}"
            )
        
        # Build response
        pagewise_line_items = []
        total_item_count = 0
        
        for page_data in extracted_pages:
            # Convert to Pydantic models
            bill_items = [
                BillItem(**item) for item in page_data['bill_items']
            ]
            
            pagewise_item = PagewiseLineItems(
                page_no=page_data['page_no'],
                page_type=page_data['page_type'],
                bill_items=bill_items
            )
            
            pagewise_line_items.append(pagewise_item)
            total_item_count += len(bill_items)
        
        # Create response
        response = BillExtractionResponse(
            is_success=True,
            token_usage=TokenUsage(**token_usage),
            data=BillExtractionData(
                pagewise_line_items=pagewise_line_items,
                total_item_count=total_item_count
            )
        )
        
        logger.info(f"Successfully extracted {total_item_count} items")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_file_path:
            cleanup_temp_file(temp_file_path)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "is_success": False,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Custom exception handler for general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "is_success": False,
            "message": "Internal server error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

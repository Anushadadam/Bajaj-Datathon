import os
import asyncio
import logging
from app.main import extract_bill_data
from app.models import BillExtractionRequest

# Configure logging
logging.getLogger("app.llm_extractor").setLevel(logging.DEBUG)
logging.getLogger("app.main").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Force model to flash (commented out to use default)
# os.environ["GEMINI_MODEL"] = "gemini-1.5-flash"

async def verify_samples():
    samples_dir = "/home/anusha/Bajaj-Datathon/training_samples/TRAINING_SAMPLES"
    if not os.path.exists(samples_dir):
        logger.error(f"Samples directory not found: {samples_dir}")
        return

    files = [f for f in os.listdir(samples_dir) if f.endswith('.pdf') or f.endswith('.jpg') or f.endswith('.png')]
    files.sort()
    
    # Process all samples
    for filename in files:
        file_path = os.path.join(samples_dir, filename)
        # We need a URL for the API, but for local testing we might need to mock download_document 
        # or just pass a file path if we modify the code temporarily.
        # However, the current implementation expects a URL.
        # Let's see if we can use a file:// URL.
        file_url = f"file://{file_path}"
        
        logger.info(f"Processing {filename}...")
        try:
            request = BillExtractionRequest(document=file_url)
            # We need to mock the download_document function to handle file:// URLs 
            # or just rely on requests.get handling it (which it might not for local files depending on adapter).
            # Actually, requests doesn't support file:// by default.
            # So I'll need to patch download_document in this script.
            
            from unittest.mock import patch
            
            with patch('app.main.download_document') as mock_download, \
                 patch('app.main.validate_document_url') as mock_validate, \
                 patch('app.main.cleanup_temp_file') as mock_cleanup:
                
                # Mock return value: (temp_file_path, file_ext)
                mock_download.return_value = (file_path, os.path.splitext(filename)[1])
                # Mock validation to always return True
                mock_validate.return_value = True
                # Mock cleanup to do nothing
                mock_cleanup.return_value = None
                
                response = await extract_bill_data(request)
                
                if response.is_success:
                    data = response.data
                    calculated_total = sum(item.item_amount for page in data.pagewise_line_items for item in page.bill_items)
                    detected_total = sum(page.detected_total_amount for page in data.pagewise_line_items)
                    
                    logger.info(f"Sample: {filename}")
                    logger.info(f"  Calculated Total: {calculated_total}")
                    logger.info(f"  Detected Total: {detected_total}")
                    logger.info(f"  Items: {data.total_item_count}")
                else:
                    logger.error(f"Failed to process {filename}")
                    
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(verify_samples())

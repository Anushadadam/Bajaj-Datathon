"""Test script to process all training samples and generate accuracy report"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ocr_processor import OCRProcessor
from app.llm_extractor import LLMExtractor
from app.utils import is_pdf


class TrainingSampleTester:
    """Test the extraction pipeline on training samples"""
    
    def __init__(self, samples_dir: str):
        self.samples_dir = samples_dir
        self.ocr_processor = OCRProcessor()
        self.llm_extractor = LLMExtractor()
        self.results = []
    
    def process_sample(self, file_path: str) -> Dict[str, Any]:
        """Process a single training sample"""
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(file_path)}")
        print(f"{'='*60}")
        
        try:
            # Extract text using OCR
            is_pdf_file = is_pdf(file_path)
            page_texts = self.ocr_processor.process_document(file_path, is_pdf=is_pdf_file)
            print(f"✓ Extracted text from {len(page_texts)} pages")
            
            # Extract structured data using LLM
            extracted_pages, token_usage = self.llm_extractor.extract_from_document(page_texts)
            print(f"✓ Extracted data from {len(extracted_pages)} pages")
            
            # Calculate totals
            total_items = 0
            total_amount = 0.0
            
            for page_data in extracted_pages:
                page_items = len(page_data['bill_items'])
                total_items += page_items
                
                for item in page_data['bill_items']:
                    total_amount += item['item_amount']
                
                print(f"  Page {page_data['page_no']} ({page_data['page_type']}): {page_items} items")
            
            print(f"\n✓ Total items: {total_items}")
            print(f"✓ Total amount: ₹{total_amount:.2f}")
            print(f"✓ Token usage: {token_usage['total_tokens']} tokens")
            
            result = {
                'file': os.path.basename(file_path),
                'success': True,
                'pages': len(extracted_pages),
                'total_items': total_items,
                'total_amount': total_amount,
                'token_usage': token_usage,
                'extracted_data': extracted_pages
            }
            
            return result
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return {
                'file': os.path.basename(file_path),
                'success': False,
                'error': str(e)
            }
    
    def run_all_tests(self):
        """Run tests on all training samples"""
        # Get all PDF files
        sample_files = sorted(Path(self.samples_dir).glob("*.pdf"))
        
        if not sample_files:
            print(f"No PDF files found in {self.samples_dir}")
            return
        
        print(f"Found {len(sample_files)} training samples")
        
        # Process each sample
        for sample_file in sample_files:
            result = self.process_sample(str(sample_file))
            self.results.append(result)
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        print(f"\n\n{'='*60}")
        print("TEST REPORT")
        print(f"{'='*60}\n")
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"Total samples: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            print(f"\n{'='*60}")
            print("SUCCESSFUL EXTRACTIONS")
            print(f"{'='*60}\n")
            
            total_items = sum(r['total_items'] for r in successful)
            total_amount = sum(r['total_amount'] for r in successful)
            total_tokens = sum(r['token_usage']['total_tokens'] for r in successful)
            
            for result in successful:
                print(f"{result['file']:30} | Items: {result['total_items']:3} | Amount: ₹{result['total_amount']:10.2f} | Tokens: {result['token_usage']['total_tokens']:5}")
            
            print(f"\n{'Total':30} | Items: {total_items:3} | Amount: ₹{total_amount:10.2f} | Tokens: {total_tokens:5}")
            print(f"\nAverage tokens per document: {total_tokens / len(successful):.0f}")
        
        if failed:
            print(f"\n{'='*60}")
            print("FAILED EXTRACTIONS")
            print(f"{'='*60}\n")
            
            for result in failed:
                print(f"{result['file']:30} | Error: {result['error']}")
        
        # Save detailed results to JSON
        output_file = "test_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✓ Detailed results saved to: {output_file}")


def main():
    """Main function"""
    # Path to training samples
    samples_dir = "training_samples/TRAINING_SAMPLES"
    
    if not os.path.exists(samples_dir):
        print(f"Error: Training samples directory not found: {samples_dir}")
        print("Please ensure the training samples are extracted to the correct location.")
        return
    
    # Run tests
    tester = TrainingSampleTester(samples_dir)
    tester.run_all_tests()


if __name__ == "__main__":
    main()

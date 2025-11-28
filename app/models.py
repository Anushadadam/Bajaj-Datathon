"""Pydantic models for request/response validation"""
from typing import List, Literal
from pydantic import BaseModel, Field, HttpUrl


class BillExtractionRequest(BaseModel):
    """Request model for bill extraction"""
    document: str = Field(..., description="URL to the document image/PDF")


class BillItem(BaseModel):
    """Individual line item in a bill"""
    item_name: str = Field(..., description="Name of the item exactly as mentioned in the bill")
    item_amount: float = Field(..., description="Net amount of the item post discounts")
    item_rate: float = Field(..., description="Rate per unit exactly as mentioned in the bill")
    item_quantity: float = Field(..., description="Quantity exactly as mentioned in the bill")


class PagewiseLineItems(BaseModel):
    """Line items grouped by page"""
    page_no: str = Field(..., description="Page number")
    page_type: Literal["Bill Detail", "Final Bill", "Pharmacy"] = Field(
        ..., description="Type of page"
    )
    bill_items: List[BillItem] = Field(..., description="List of bill items on this page")


class TokenUsage(BaseModel):
    """Token usage information"""
    total_tokens: int = Field(..., description="Cumulative tokens from all LLM calls")
    input_tokens: int = Field(..., description="Cumulative input tokens from all LLM calls")
    output_tokens: int = Field(..., description="Cumulative output tokens from all LLM calls")


class BillExtractionData(BaseModel):
    """Extracted bill data"""
    pagewise_line_items: List[PagewiseLineItems] = Field(
        ..., description="Line items grouped by page"
    )
    total_item_count: int = Field(..., description="Total count of items across all pages")


class BillExtractionResponse(BaseModel):
    """Response model for bill extraction"""
    is_success: bool = Field(..., description="Whether the extraction was successful")
    token_usage: TokenUsage = Field(..., description="Token usage information")
    data: BillExtractionData = Field(..., description="Extracted bill data")


class ErrorResponse(BaseModel):
    """Error response model"""
    is_success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(..., description="Error message")

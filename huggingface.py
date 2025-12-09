"""
HuggingFace Inference API Service
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import re

from huggingface_hub import InferenceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables - HuggingFace Spaces provides HF_API_TOKEN or HF_TOKEN
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_TOKEN")
HF_MODEL = os.environ.get("HF_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct")
HF_PROVIDER = os.environ.get("HF_PROVIDER", "novita")
PORT = int(os.environ.get("PORT", 7860))
HOST = os.environ.get("HOST", "0.0.0.0")

# Validate HF_TOKEN - make it optional for HuggingFace Spaces (they provide it automatically)
if not HF_TOKEN:
    logger.warning(
        "HF_TOKEN not found in environment. "
        "HuggingFace Spaces should provide this automatically. "
        "If running locally, set HF_TOKEN environment variable."
    )
    # Don't raise error - let it fail gracefully when trying to use the client
    client = None
else:
    if not HF_TOKEN.startswith("hf_"):
        logger.warning(
            f"HF_TOKEN does not start with 'hf_'. Got: {HF_TOKEN[:10]}..."
        )
    
    # Initialize HuggingFace client
    try:
        client = InferenceClient(
            model=HF_MODEL,
            api_key=HF_TOKEN,
            provider=HF_PROVIDER,
        )
        logger.info(f"Initialized HuggingFace client with model: {HF_MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace client: {str(e)}")
        client = None

# Create FastAPI app
app = FastAPI(
    title="WorthWise ROI Summarization API",
    description="AI-powered summarization of college ROI analysis",
    version="1.0.0",
)

# CORS middleware - allow all origins for HuggingFace Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # HuggingFace Spaces handles CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System prompt for ROI analysis
SYSTEM_PROMPT = (
    "You are a data-driven financial analyst specializing in college ROI analysis. "
    "Critically evaluate college programs based on strict financial metrics. "
    "Not all programs deserve high ratings - be objective and critical when warranted.\n\n"
    "Provide:\n"
    "1) A concise, objective summary (1-2 paragraphs, 3-4 sentences each) that critically evaluates:\n"
    "   - The total financial investment (tuition, opportunity cost)\n"
    "   - Earning potential vs. investment (calculate approximate payback period)\n"
    "   - ROI ratio and whether it justifies the investment\n"
    "   - Realistic assessment: most programs are average (3 stars), exceptional programs are rare (4-5 stars), poor investments exist (1-2 stars)\n\n"
    "2) A 1-5 star rating at the END of your response in this exact format: 'RATING: X stars' where X is 1-5\n\n"
    "Rating Criteria (be strict and objective):\n"
    "- 5 stars: Exceptional ROI (>3.0x), strong earnings growth, payback <3 years\n"
    "- 4 stars: Good ROI (2.0-3.0x), solid earnings, payback 3-5 years\n"
    "- 3 stars: Average ROI (1.2-2.0x), moderate earnings, payback 5-8 years\n"
    "- 2 stars: Poor ROI (0.8-1.2x), low earnings growth, payback 8-12 years\n"
    "- 1 star: Very poor ROI (<0.8x), minimal earnings benefit, payback >12 years or negative ROI\n\n"
    "Use specific numbers and calculations. Be direct about poor financial decisions. "
    "Most programs should receive 2-4 stars - 5 stars are rare. "
    "If data is incomplete, note limitations but still provide objective analysis based on available metrics."
)

# Request/Response models
class SummarizeRequest(BaseModel):
    """Request model for summarization"""
    institution_name: str = Field(..., description="Name of the institution")
    major_name: str = Field(..., description="Name of the major/program")
    tuition_fees: int = Field(..., description="Annual tuition and fees (USD)")
    earnings_year_1: Optional[int] = Field(None, description="Projected earnings year 1 post-grad (USD)")
    earnings_year_3: Optional[int] = Field(None, description="Projected earnings year 3 post-grad (USD)")
    roi: Optional[float] = Field(None, description="Return on investment (ratio)")


class SummarizeResponse(BaseModel):
    """Response model with summary and rating"""
    summary: str = Field(..., description="AI-generated summary of the ROI analysis")
    rating: int = Field(..., description="1-5 star rating", ge=1, le=5)


def format_currency(amount: Optional[int]) -> str:
    """Format currency amount for display"""
    if amount is None:
        return "N/A"
    return f"${amount:,}"


def format_number(value: Optional[float], decimals: int = 2) -> str:
    """Format number for display"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def extract_rating(text: str) -> int:
    """
    Extract rating from text. Looks for patterns like:
    - "RATING: 5 stars"
    - "RATING: 4 stars"
    - "Rating: 3 stars"
    """
    # Try to find rating pattern
    patterns = [
        r'RATING:\s*(\d+)\s*stars?',
        r'Rating:\s*(\d+)\s*stars?',
        r'rating:\s*(\d+)\s*stars?',
        r'(\d+)\s*stars?\s*rating',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rating = int(match.group(1))
            if 1 <= rating <= 5:
                return rating
    
    # If no explicit rating found, try to infer from text
    # Look for phrases that might indicate rating
    text_lower = text.lower()
    if any(word in text_lower for word in ['excellent', 'outstanding', 'exceptional', 'highly recommended']):
        return 5
    elif any(word in text_lower for word in ['very good', 'strong', 'recommended', 'solid']):
        return 4
    elif any(word in text_lower for word in ['good', 'reasonable', 'decent', 'acceptable']):
        return 3
    elif any(word in text_lower for word in ['fair', 'moderate', 'average', 'adequate']):
        return 2
    else:
        return 1  # Default to 1 if unclear


def clean_summary(text: str) -> str:
    """Remove rating line from summary text"""
    # Remove rating patterns
    patterns = [
        r'RATING:\s*\d+\s*stars?.*$',
        r'Rating:\s*\d+\s*stars?.*$',
        r'rating:\s*\d+\s*stars?.*$',
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    return text.strip()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "WorthWise ROI Summarization API",
        "status": "running",
        "model": HF_MODEL,
        "client_initialized": client is not None,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if client is not None else "unhealthy",
        "model": HF_MODEL,
        "client_initialized": client is not None,
    }


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Generate AI-powered summary of ROI analysis with rating
    
    Takes financial data (tuition, earnings, ROI) and generates
    a human-readable summary with a 1-5 star rating.
    """
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="HuggingFace client not initialized. Please check HF_TOKEN environment variable."
        )
    
    try:
        # Build user prompt with formatted data
        user_prompt = (
            f"Institution: {request.institution_name}\n"
            f"Major/Program: {request.major_name}\n"
            f"Annual Tuition and Fees: {format_currency(request.tuition_fees)}\n"
            f"Year 1 Earnings: {format_currency(request.earnings_year_1)}\n"
            f"Year 3 Earnings: {format_currency(request.earnings_year_3)}\n"
        )
        
        if request.roi is not None:
            user_prompt += f"Return on Investment: {format_number(request.roi)}x\n"
        
        user_prompt += (
            "\nPlease provide a comprehensive financial analysis summary based on this data. "
            "Focus on the value proposition, financial feasibility, and career prospects. "
            "End your response with 'RATING: X stars' where X is a number from 1 to 5."
        )
        
        # Call HuggingFace API
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=600,
            temperature=0.4,
            top_p=0.9,
        )
        
        # Extract content from response
        try:
            content = response.choices[0].message["content"]
        except (KeyError, TypeError, IndexError):
            try:
                content = response.choices[0].message.content
            except (AttributeError, IndexError):
                if hasattr(response, "content"):
                    content = response.content
                elif isinstance(response, str):
                    content = response
                else:
                    content = str(response)
        
        if not content or not content.strip():
            raise ValueError("Empty response from HuggingFace API")
        
        # Extract rating and clean summary
        rating = extract_rating(content)
        summary = clean_summary(content)
        
        # If summary is empty after cleaning, use original
        if not summary:
            summary = content
        
        logger.info(f"Generated summary with rating: {rating} stars")
        
        return SummarizeResponse(
            summary=summary,
            rating=rating
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)


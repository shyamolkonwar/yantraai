"""
Demo Pipeline using GPT-4o Vision for Investor Demo

This module provides a "Wizard of Oz" backend that uses OpenAI's GPT-4o Vision
to process complex documents (curly brace grouping, Hinglish text) for demo purposes.

For production, this will be replaced with fine-tuned local models.
"""

import base64
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from parent directory's .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")


class DemoPipeline:
    """Demo pipeline using GPT-4o Vision API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the demo pipeline
        
        Args:
            api_key: OpenAI API key (if not provided, reads from OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def process_document(self, image_path: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process document using GPT-4o Vision
        
        Args:
            image_path: Path to document image
            job_id: Optional job ID (generated if not provided)
            
        Returns:
            Structured JSON result matching Truth Layer schema
        """
        print(f"🚀 Truth Layer Demo: Processing {image_path}...")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Generate job ID if not provided
        if not job_id:
            job_id = str(uuid.uuid4())
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Construct the prompt
        prompt = """
You are the "Truth Layer" AI engine. Your job is to extract structured data from messy Indian documents (prescriptions, invoices, forms).

CRITICAL RULES:
1. READ EVERYTHING: Capture both printed headers and handwritten notes.
2. HANDLE GROUPING: If a curly brace '{' groups multiple items (e.g., medicines) to one instruction (e.g., "after meals"), apply that instruction to ALL grouped items.
3. HINDI/HINGLISH: Transliterate any Hindi or Hinglish text to English.
4. PII DETECTION: Identify PII (Names, Dates, Phone Numbers, Addresses).
5. TRUST SCORING: Assign a confidence score (0.0 to 1.0) based on legibility and clarity.
6. DOCUMENT TYPE: Identify if this is a prescription, invoice, form, or other document type.

OUTPUT SCHEMA (JSON ONLY):
{
  "job_id": "uuid",
  "status": "done",
  "document_type": "prescription | invoice | form | other",
  "pages": 1,
  "fields": [
    {
      "region_id": "string (e.g., 'region_1', 'region_2')",
      "page": 1,
      "bbox": [x1, y1, x2, y2],
      "label": "string (e.g., 'medicine_name', 'dosage', 'patient_name', 'date')",
      "raw_text": "string (extracted text)",
      "ocr_conf": float (0.0-1.0),
      "normalized_text": "string (cleaned/transliterated text)",
      "trans_conf": float (0.0-1.0),
      "pii": [
        {
          "type": "PERSON | DATE | PHONE | ADDRESS | null",
          "span": [start_char, end_char],
          "confidence": float (0.0-1.0)
        }
      ],
      "trust_score": float (0.0-1.0),
      "human_verified": false,
      "verified_value": null
    }
  ],
  "created_at": "ISO timestamp",
  "processing_meta": {
    "layout_model": "gpt-4o-vision",
    "ocr_model": "gpt-4o-vision",
    "lingua_model": "gpt-4o-vision"
  }
}

IMPORTANT:
- For curly brace grouping, create separate field entries for each grouped item, but include the shared instruction in a "instructions" field or in the normalized_text.
- Estimate reasonable bounding boxes based on typical document layouts.
- Be thorough - extract ALL visible text, both printed and handwritten.
- Return ONLY valid JSON, no additional text.
"""
        
        try:
            # Call GPT-4o Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Deterministic output
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure job_id is set
            result["job_id"] = job_id
            
            # Ensure status is set
            if "status" not in result:
                result["status"] = "done"
            
            # Ensure created_at is set
            if "created_at" not in result:
                result["created_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Ensure processing_meta is set
            if "processing_meta" not in result:
                result["processing_meta"] = {
                    "layout_model": "gpt-4o-vision",
                    "ocr_model": "gpt-4o-vision",
                    "lingua_model": "gpt-4o-vision"
                }
            
            print("✅ Truth Layer Extraction Complete")
            return result
            
        except Exception as e:
            print(f"❌ Error processing document: {e}")
            raise
    
    def save_result(self, result: Dict[str, Any], output_path: str):
        """
        Save result to JSON file
        
        Args:
            result: Processing result
            output_path: Path to save JSON file
        """
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"💾 Saved result to {output_path}")


def run_demo(image_path: str, output_path: str = "demo_result.json"):
    """
    Run demo pipeline on a single image

    Args:
        image_path: Path to image file
        output_path: Path to save result JSON
    """
    pipeline = DemoPipeline()
    result = pipeline.process_document(image_path)
    pipeline.save_result(result, output_path)

    # Create demo preview without processing_meta
    demo_result = {k: v for k, v in result.items() if k != "processing_meta"}

    print("\n" + "="*60)
    print("RESULT PREVIEW")
    print("="*60)
    print(json.dumps(demo_result, indent=2))
    print("="*60)


if __name__ == "__main__":
    import sys
    
    # Check for image file argument
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
    else:
        # Default to looking for common test images
        test_images = ["image_fbd36c.jpg", "test_prescription.jpg", "sample.jpg", "test.png"]
        image_file = None
        
        for img in test_images:
            if os.path.exists(img):
                image_file = img
                break
        
        if not image_file:
            print("❌ No image file found.")
            print("Usage: python demo_pipeline.py <image_path>")
            print("Or place a test image in the current directory with one of these names:")
            print("  - image_fbd36c.jpg")
            print("  - test_prescription.jpg")
            print("  - sample.jpg")
            print("  - test.png")
            sys.exit(1)
    
    if not os.path.exists(image_file):
        print(f"❌ Image file not found: {image_file}")
        sys.exit(1)
    
    run_demo(image_file)

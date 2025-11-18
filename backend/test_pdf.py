#!/usr/bin/env python3
"""
Simple test script to upload and process the test PDF
"""

import requests
import time
import os

# API endpoint
BASE_URL = "http://localhost:8000/api/v1"

def test_pdf_processing():
    """Test PDF processing locally"""

    # Path to test PDF
    pdf_path = "../testing/image.pdf"

    if not os.path.exists(pdf_path):
        print(f"Test PDF not found at {pdf_path}")
        return

    print("Starting PDF processing test...")

    # Step 1: Process PDF directly
    print("1. Processing PDF...")
    with open(pdf_path, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/jobs/process", files=files)

    if response.status_code != 200:
        print(f"Processing failed: {response.status_code} - {response.text}")
        return

    result_data = response.json()
    print("✓ PDF processed successfully!")

    # Step 2: Display results
    print("2. Processing results:")

    job_info = result_data.get('job', {})
    pages = result_data.get('pages', [])
    regions = result_data.get('regions', [])

    print(f"   Job ID: {job_info.get('id')}")
    print(f"   Filename: {job_info.get('original_filename')}")
    print(f"   Status: {job_info.get('status')}")
    print(f"   Pages processed: {len(pages)}")
    print(f"   Total regions: {len(regions)}")

    # Show page details
    for page in pages[:2]:  # Show first 2 pages
        print(f"   Page {page['page_number']}: {page['width']}x{page['height']}")

    # Show region details
    print("   Sample regions:")
    for i, region in enumerate(regions[:5]):  # Show first 5 regions
        label = region.get('label', 'unknown')
        text = region.get('normalized_text', '')[:60] + '...' if len(region.get('normalized_text', '')) > 60 else region.get('normalized_text', '')
        trust_score = region.get('trust_score', 0)
        pii_count = len(region.get('pii_detected', []))
        print(f"     {i+1}. {label}: {text}")
        print(f"        Trust Score: {trust_score:.2f}, PII Entities: {pii_count}")

    # Calculate summary statistics
    if regions:
        avg_trust = sum(r.get('trust_score', 0) for r in regions) / len(regions)
        total_pii = sum(len(r.get('pii_detected', [])) for r in regions)
        print(f"\n   Summary:")
        print(f"   Average Trust Score: {avg_trust:.2f}")
        print(f"   Total PII Entities Detected: {total_pii}")

    print("\n✓ Test completed successfully!")
    print("The backend is working with local ML processing!")

if __name__ == "__main__":
    test_pdf_processing()

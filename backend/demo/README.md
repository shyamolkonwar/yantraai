# Demo Folder

This folder contains all demo-related scripts and assets for the investor demo.

## Contents

### Core Scripts
- **[demo_pipeline.py](demo_pipeline.py)** - GPT-4o Vision pipeline for demo mode
- **[test_demo_setup.py](test_demo_setup.py)** - System verification script

### Documentation
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - Comprehensive demo guide with setup, narrative, and Q&A
- **[QUICK_START.md](QUICK_START.md)** - Quick reference for demo day

### Assets
- **[demo_samples/](demo_samples/)** - Sample documents for testing
  - `prescription_sample.png` - Medical prescription with curly brace grouping
  - `README.md` - Documentation for samples

### Results
- **demo_result.json** - Latest test result from demo pipeline

## Quick Start

### 1. Verify Setup
```bash
cd /Users/shyamolkonwar/Documents/Yantra\ AI/mvp/backend/demo
python test_demo_setup.py
```

### 2. Test Pipeline
```bash
export $(cat ../.env | grep -v '^#' | xargs)
python demo_pipeline.py demo_samples/prescription_sample.png
```

### 3. Run Full Demo
See [QUICK_START.md](QUICK_START.md) for complete instructions.

## Configuration

The demo mode is controlled by environment variables in `backend/.env`:
- `DEMO_MODE=true` - Enables GPT-4o Vision pipeline
- `OPENAI_API_KEY=sk-...` - Your OpenAI API key

## How It Works

When `DEMO_MODE=true`, the orchestrator automatically uses `demo_pipeline.py` instead of the local OCR pipeline. This provides:
- ✅ Curly brace grouping understanding
- ✅ Hinglish/Hindi transliteration
- ✅ PII detection
- ✅ Trust scoring
- ✅ Clean, structured JSON output

## After Demo

To switch back to local pipeline:
1. Set `DEMO_MODE=false` in `backend/.env`
2. Restart the backend server

---

**For detailed instructions, see [DEMO_GUIDE.md](DEMO_GUIDE.md)**

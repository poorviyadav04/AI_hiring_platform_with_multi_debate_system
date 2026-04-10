# Installation Guide - Python 3.13 Compatibility

## Issue
You're using **Python 3.13.0**, which removed the `distutils` module. Many older packages in `requirements.txt` don't support Python 3.13 yet.

## Quick Solution for Dashboard

Install only the essential packages needed for the dashboard:

```bash
# In your activated venv
pip install streamlit plotly pandas pydantic python-dotenv
```

Then run the dashboard:
```bash
streamlit run dashboard/app.py
```

## For Full System (Recommended)

### Option 1: Use Python 3.11 (Best)

1. **Download Python 3.11** from https://www.python.org/downloads/
2. **Install** it (make sure to check "Add to PATH")
3. **Recreate venv:**
```bash
# Remove old venv
rmdir /s venv

# Create new venv with Python 3.11
py -3.11 -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

### Option 2: Install setuptools with distutils support

```bash
pip install setuptools
```

Then try:
```bash
pip install -r requirements.txt --use-deprecated=legacy-resolver
```

## What Works Right Now

Your **core system** (Phases 1-9) already works because you built it with your base Python installation. The dashboard just needs:
- streamlit
- plotly
- pandas
- pydantic

## Testing

After installing the minimal dependencies:

```bash
# Test dashboard
streamlit run dashboard/app.py

# If you need full system including LLM/RAG:
# Use Python 3.11 approach above
```

## Status

- ✅ **Phases 1-9:** Working (built with base Python)
- 🟡 **Phase 10 (Dashboard):** Needs minimal deps (streamlit, plotly)
- 🟡 **Full venv:** Needs Python 3.11 for all packages

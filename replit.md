# HCC Prototype

## Overview
A Streamlit-based AI-Assisted Clinical Coder application for CMS-HCC Version 28 (v28 model). Built for Humana to assist with HCC (Hierarchical Condition Category) coding and RAF (Risk Adjustment Factor) score calculation.

## Architecture
- **Language**: Python 3.12
- **Framework**: Streamlit
- **Key Libraries**: pandas, streamlit

## Project Structure
- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies

## Running the App
The app runs on port 5000 via Streamlit:
```
streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
```

## Features
- V28 HCC mapping with ICD-10 codes and coefficients
- RAF score calculation with interaction bonuses
- Clinical documentation review interface
- Confirm/Reject workflow for HCC conditions

## Deployment
- Host: 0.0.0.0
- Port: 5000
- Output type: webview

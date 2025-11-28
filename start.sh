#!/bin/bash

# Quick Start Script for Bill Extraction API

echo "========================================="
echo "Bill Extraction API - Quick Start"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - GOOGLE_CLOUD_VISION_API_KEY"
    echo "   - GOOGLE_GEMINI_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "========================================="
echo "Available Commands:"
echo "========================================="
echo ""
echo "1. Start API Server:"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload"
echo ""
echo "2. Test with Training Samples:"
echo "   python test_samples.py"
echo ""
echo "3. Run Unit Tests:"
echo "   pytest tests/ -v"
echo ""
echo "4. Build Docker Image:"
echo "   docker build -t bill-extraction-api ."
echo ""
echo "5. Run Docker Container:"
echo "   docker run -p 3000:3000 --env-file .env bill-extraction-api"
echo ""
echo "========================================="
echo ""

# Ask if user wants to start the server
read -p "Start API server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting API server..."
    uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
fi

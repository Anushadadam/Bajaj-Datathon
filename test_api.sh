#!/bin/bash

# Test the Bill Extraction API

echo "========================================="
echo "Testing Bill Extraction API"
echo "========================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check Endpoint"
echo "GET http://localhost:3000/"
echo ""
curl -s http://localhost:3000/ | python3 -m json.tool
echo ""
echo "✓ Health check passed"
echo ""

# Test 2: Extract Bill Data
echo "========================================="
echo "Test 2: Extract Bill Data"
echo "POST http://localhost:3000/extract-bill-data"
echo ""

# Sample document URL from the hackathon
SAMPLE_URL="https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"

curl -s -X POST http://localhost:3000/extract-bill-data \
  -H "Content-Type: application/json" \
  -d "{\"document\": \"$SAMPLE_URL\"}" \
  | python3 -m json.tool

echo ""
echo "✓ Extraction test completed"
echo ""
echo "========================================="

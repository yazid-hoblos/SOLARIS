#!/bin/bash
# Start SOLARIS Chatbot GUI

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🧬 SOLARIS Chatbot GUI Starting...             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Opening chatbot at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask server
python3 api.py

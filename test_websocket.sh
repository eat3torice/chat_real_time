#!/bin/bash
# Simple WebSocket test using wscat (if installed)
# Install: npm install -g wscat

echo "Testing WebSocket endpoint..."
echo "If you have wscat installed, run:"
echo "wscat -c ws://127.0.0.1:8000/ws/1"
echo ""
echo "Or use the Python test script:"
echo "python test_websocket.py"
echo ""
echo "Or open the HTML test client in browser:"
echo "http://localhost:8080/test_websocket.html"
#!/bin/bash
# Local development script

set -e

echo "🚀 Starting Agentic Job Search locally..."
echo ""

# Check for API key
if [ -z "$GOOGLE_API_KEY" ]; then
    if [ -f "backend/.env" ]; then
        export $(grep -v '^#' backend/.env | xargs)
    fi

    if [ -z "$GOOGLE_API_KEY" ]; then
        echo "❌ GOOGLE_API_KEY not set"
        echo "   Set it via: export GOOGLE_API_KEY=your_key"
        echo "   Or create backend/.env file"
        exit 1
    fi
fi

echo "✅ API key found"

# Start backend
echo ""
echo "📦 Starting backend..."
cd backend
pip install -r requirements.txt -q
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3

# Start frontend
echo ""
echo "🎨 Starting frontend..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ App running!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

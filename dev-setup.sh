#!/bin/bash

# Poe Server Bot Development Helper Script

set -e

echo "🤖 Poe Server Bot Development Environment Setup"
echo "================================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "📝 Please edit .env file with your actual credentials"
    echo ""
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if Modal is configured
echo "🚀 Checking Modal configuration..."
if command -v modal &> /dev/null; then
    if modal token list &> /dev/null; then
        echo "✅ Modal is configured and ready"
    else
        echo "⚠️  Modal token not found. Run 'modal token new' to authenticate"
    fi
else
    echo "⚠️  Modal CLI not found. Installing..."
    pip install modal
    echo "✅ Modal CLI installed. Run 'modal token new' to authenticate"
fi
echo ""

# Display helpful commands
echo "🛠️  Helpful Development Commands:"
echo "================================="
echo "• Run bot locally:     python echobot.py"
echo "• Deploy to Modal:     modal deploy echobot.py"
echo "• Modal logs:          modal logs <app-name>"
echo "• Modal token setup:   modal token new"
echo ""

echo "📚 Next Steps:"
echo "=============="
echo "1. Edit .env file with your Poe bot credentials"
echo "2. Test locally: python echobot.py"
echo "3. Deploy: modal deploy echobot.py"
echo "4. Update your Poe bot's server URL with the Modal endpoint"
echo ""

echo "🎉 Development environment ready!"
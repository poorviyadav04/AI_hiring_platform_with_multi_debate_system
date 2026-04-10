#!/usr/bin/env bash
# Setup script for LLM Decision Intelligence System
# This script installs Ollama and downloads required models

set -e  # Exit on error

echo "🧠 LLM Decision Intelligence System - Setup"
echo "==========================================="
echo ""

# Check if running on Windows (Git Bash or WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "⚠️  Windows detected. Please install Ollama manually:"
    echo "   1. Download from https://ollama.ai/download"
    echo "   2. Run the installer"
    echo "   3. Open a new terminal and run this script again"
    echo ""
    read -p "Have you installed Ollama? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Please install Ollama first, then run this script again."
        exit 1
    fi
else
    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        echo "✓ Ollama is already installed"
    else
        echo "📦 Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        echo "✓ Ollama installed successfully"
    fi
fi

echo ""
echo "🔍 Checking Ollama service..."
if ! ollama list &> /dev/null; then
    echo "⚠️  Ollama service is not running. Please start it:"
    echo "   - On Windows: Ollama should start automatically"
    echo "   - On Linux/Mac: Run 'ollama serve' in another terminal"
    echo ""
    read -p "Press Enter when Ollama is running..."
fi

echo ""
echo "📥 Downloading LLM models (this may take a while)..."
echo ""

# Download Llama 3 (8B) - Primary model
echo "1️⃣  Downloading Llama 3 (8B)..."
ollama pull llama3
echo "✓ Llama 3 downloaded"

echo ""
echo "2️⃣  Downloading Mistral (7B)..."
ollama pull mistral
echo "✓ Mistral downloaded"

echo ""
echo "3️⃣  Downloading Phi-3 Mini (3.8B)..."
ollama pull phi3
echo "✓ Phi-3 downloaded"

echo ""
echo "==========================================="
echo "✅ Ollama setup complete!"
echo ""
echo "📋 Installed models:"
ollama list
echo ""
echo "🎉 You're ready to proceed with the project!"

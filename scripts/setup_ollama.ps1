# Setup script for LLM Decision Intelligence System (PowerShell)
# This script helps install Ollama and download models on Windows

Write-Host "🧠 LLM Decision Intelligence System - Setup" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
$ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $ollamaInstalled) {
    Write-Host "⚠️  Ollama is not installed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Ollama:" -ForegroundColor White
    Write-Host "  1. Visit https://ollama.ai/download" -ForegroundColor White
    Write-Host "  2. Download the Windows installer" -ForegroundColor White
    Write-Host "  3. Run the installer" -ForegroundColor White
    Write-Host "  4. Restart this script" -ForegroundColor White
    Write-Host ""
    
    $openBrowser = Read-Host "Open download page in browser? (y/n)"
    if ($openBrowser -eq 'y') {
        Start-Process "https://ollama.ai/download"
    }
    
    exit 1
}

Write-Host "✓ Ollama is installed" -ForegroundColor Green
Write-Host ""

# Check if Ollama service is running
Write-Host "🔍 Checking Ollama service..." -ForegroundColor Cyan
try {
    $null = ollama list 2>&1
    Write-Host "✓ Ollama service is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ollama service may not be running" -ForegroundColor Yellow
    Write-Host "   Ollama should start automatically on Windows" -ForegroundColor White
    Write-Host "   If you see errors, try restarting your computer" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to continue..."
}

Write-Host ""
Write-Host "📥 Downloading LLM models..." -ForegroundColor Cyan
Write-Host "   (This may take 10-30 minutes depending on your internet speed)" -ForegroundColor Yellow
Write-Host ""

# Download models
Write-Host "1️⃣  Downloading Llama 3 (8B - ~4.7GB)..." -ForegroundColor White
ollama pull llama3
Write-Host "✓ Llama 3 downloaded" -ForegroundColor Green

Write-Host ""
Write-Host "2️⃣  Downloading Mistral (7B - ~4.1GB)..." -ForegroundColor White
ollama pull mistral
Write-Host "✓ Mistral downloaded" -ForegroundColor Green

Write-Host ""
Write-Host "3️⃣  Downloading Phi-3 Mini (3.8B - ~2.3GB)..." -ForegroundColor White
ollama pull phi3
Write-Host "✓ Phi-3 downloaded" -ForegroundColor Green

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "✅ Ollama setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Installed models:" -ForegroundColor Cyan
ollama list
Write-Host ""
Write-Host "🎉 You're ready to proceed with the project!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Install Python dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "  2. Copy .env.example to .env and configure if needed" -ForegroundColor White
Write-Host "  3. Run the API: uvicorn api.main:app --reload" -ForegroundColor White

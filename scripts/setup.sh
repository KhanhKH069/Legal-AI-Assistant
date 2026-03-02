#!/bin/bash
echo "Setting up HR AI Agent..."
uv venv
source venv/bin/activate
uv pip install -r requirements.txt
cp config/.env.example .env
echo "✅ Setup complete! Edit .env with your API key"

#!/bin/bash
echo "Setting up HR AI Agent..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/.env.example .env
echo "✅ Setup complete! Edit .env with your API key"

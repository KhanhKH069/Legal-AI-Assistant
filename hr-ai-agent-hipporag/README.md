# 🤖 HR AI Agent - Gemini Version

Enterprise-grade HR AI Agent powered by **Google Gemini API**.

## 🚀 Quick Start

```bash
# 1. Install
uv pip install -r requirements.txt

# 2. Get Gemini API Key
# Go to: https://makersuite.google.com/app/apikey
# Create API key and copy it

# 3. Configure
cp config/.env.example .env
# Edit .env: GOOGLE_API_KEY=your-key-here

# 4. Run!
python main.py
```

## ✨ Features

- ✅ **Powered by Google Gemini** - Fast & cost-effective
- ✅ API Gateway (Auth + Rate Limiting)
- ✅ Admin Panel (Config + Monitoring)
- ✅ Orchestrator Agent (Intent Routing)
- ✅ Policy Agent (HR Policies)
- ✅ Onboard Agent (Employee Onboarding)
- ✅ SQL Database (SQLite/PostgreSQL)
- ✅ Audit Logging
- ✅ Production Ready

## 🎯 Architecture

```
User → API Gateway → Orchestrator → Agents → SQL Database
                                    (Gemini AI)
```

## 📊 Gemini Models

| Model | Context | Best For |
|-------|---------|----------|
| `gemini-pro` | 32K | General tasks (Default) |
| `gemini-1.5-pro` | 1M | Advanced tasks |

## 🔧 Configuration

Edit `.env`:
```env
GOOGLE_API_KEY=your-google-api-key
MODEL_NAME=gemini-pro
TEMPERATURE=0.7
```

## 📚 Documentation

- `GEMINI_MIGRATION_GUIDE.md` - Migration details
- `PROJECT_TREE_COMPLETE.md` - Project structure
- `VSCODE_SETUP_GUIDE.md` - VSCode setup

## 💡 Why Gemini?

- ✅ Free tier (60 requests/min)
- ✅ Large context (up to 1M tokens)
- ✅ Multimodal support
- ✅ Fast response times
- ✅ Cost effective

---

**Made with ❤️ using LangChain, LangGraph, and Google Gemini**

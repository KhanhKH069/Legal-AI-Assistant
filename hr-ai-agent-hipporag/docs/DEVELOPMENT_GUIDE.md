# Development Guide

## Setup Development Environment

```bash
# Clone repository
git clone <repo>
cd hr-ai-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Configure
cp config/.env.example .env
# Edit .env with your API key
```

## Project Structure

```
src/
├── core/       # Core infrastructure
├── agents/     # Agent implementations
├── services/   # Shared services
├── tools/      # Agent tools
├── data/       # Knowledge base
└── utils/      # Utilities
```

## Adding a New Agent

1. Create agent file in `src/agents/`
2. Define agent prompts and tools
3. Add to orchestrator routing
4. Write tests
5. Update documentation

## Running Tests

```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_agents.py

# With coverage
pytest --cov=src tests/
```

## Code Style

We use:
- Black for formatting
- Flake8 for linting
- MyPy for type checking

```bash
black src/
flake8 src/
mypy src/
```

## Contributing

1. Create feature branch
2. Make changes
3. Write tests
4. Run code quality checks
5. Submit PR

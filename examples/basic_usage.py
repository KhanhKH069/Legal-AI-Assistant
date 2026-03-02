"""Basic Usage Example"""
import sys

sys.path.insert(0, "../src")

from main import HRAgentApp  # type: ignore[import-not-found,attr-defined]

# Initialize
app = HRAgentApp()

# Chat
response = app.chat(user_id="user001", message="Công ty có bao nhiêu ngày phép?")

print(response)

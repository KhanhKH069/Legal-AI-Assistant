"""Advanced Usage Example"""
import sys

sys.path.insert(0, '../src')

from main import HRAgentApp

app = HRAgentApp()

# Multiple conversations
questions = [
    "Công ty có bao nhiêu ngày phép?",
    "Nhân viên mới cần giấy tờ gì?",
]

for q in questions:
    response = app.chat("user001", q)
    print(f"Q: {q}")
    print(f"A: {response['response']}\n")

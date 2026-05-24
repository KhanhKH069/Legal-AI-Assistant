import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.agents.offline_agent import answer_question

ans = answer_question("Tôi còn bao nhiêu ngày nghỉ phép?")
print(ans)

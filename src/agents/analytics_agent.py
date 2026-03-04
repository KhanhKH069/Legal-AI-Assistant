import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from src.core.config import config


def get_analytics_agent():
    """Tạo Pandas DataFrame agent để query HR Data (CSV)."""

    # Check for API key
    if config.enable_offline_mode or not config.google_api_key:
        return None

    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "hr_mock_data.csv",
    )

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return None

    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=0.0,  # Strict for data tasks
    )

    agent = create_pandas_dataframe_agent(
        llm, df, verbose=False, agent_type="tool-calling", allow_dangerous_code=True
    )
    return agent


def query_hr_data(query: str) -> str:
    """Send natural language query to the data agent"""
    agent = get_analytics_agent()
    if not agent:
        return "Xin lỗi, tính năng phân tích dữ liệu đang bị tắt (thiếu API Key hoặc CSV file)."

    try:
        response = agent.invoke({"input": query})
        return response["output"]
    except Exception as e:
        return f"Lỗi khi truy vấn dữ liệu: {e}"

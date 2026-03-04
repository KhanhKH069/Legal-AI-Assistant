from langchain_core.tools import tool
from langchain.chains import LLMMathChain
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import config


@tool
def calculate_math_expression(expression: str) -> str:
    """Evaluate a mathematical expression.

    Useful when you need to answer questions about math or perform calculations
    (e.g., calculating prorated salary, leave days deduction, or simple arithmetic).

    Args:
        expression: A mathematical expression in text or symbols (e.g., '10 * 3', '25.5 / 2').

    Returns:
        The calculated numerical result as a string.
    """
    if config.enable_offline_mode or not config.google_api_key:
        return "Calculation error: Offline mode is active, LLMMathChain cannot be initialized."

    try:
        # We initialize the LLM strictly with temp 0 for accurate math
        math_llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=0.0,
        )

        calculator = LLMMathChain.from_llm(llm=math_llm, verbose=False)
        result = calculator.run(expression)
        return str(result)
    except Exception as e:
        return f"Could not calculate the expression '{expression}'. Error: {e}"

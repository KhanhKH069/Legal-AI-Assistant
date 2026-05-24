import os
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ["GOOGLE_API_KEY"] = "AIzaSyDEcL9ftbWeeG18B-Kli-wsblUbMBo_CMk"

models = [
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-3.5-flash",
    "gemini-2.0-flash-lite",
    "gemma-4-31b-it",
    "gemini-3-pro-preview",
]

working_models = []
for model in models:
    try:
        print(f"Testing {model}...")
        llm = ChatGoogleGenerativeAI(model=model, temperature=0.0, max_retries=0)
        res = llm.invoke([HumanMessage(content="Hello")])
        print(f"SUCCESS: {model}")
        working_models.append(model)
    except Exception as e:
        print(f"FAILED {model}: {e}")

print("Working models:", working_models)

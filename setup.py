from setuptools import find_packages, setup

setup(
    name="hr-ai-agent",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "langchain==0.1.0",
        "langchain-core==0.1.10",
        "langchain-anthropic==0.1.1",
        "langgraph==0.0.20",
        "anthropic==0.18.1",
    ],
)

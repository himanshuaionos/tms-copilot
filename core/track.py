# Importing Libraries.
import os
from dotenv import load_dotenv

load_dotenv()

# LangSmith Integration.
def langsmith_integration():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv('LANGCHAIN_ENDPOINT')
    os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGSMITH_API_KEY')
    os.environ["LANGCHAIN_PROJECT"] = os.getenv('LANGCHAIN_PROJECT')
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
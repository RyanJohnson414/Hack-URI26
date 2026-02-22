import google.generativeai as genai
import os
from dotenv import load_dotenv


load_dotenv()
KEY = os.getenv("KEY")
genai.configure(api_key=KEY)
model = genai.GenerativeModel("gemini-3-flash-preview")



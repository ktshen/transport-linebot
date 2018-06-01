import os
from dotenv import load_dotenv

# Load envirnoment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

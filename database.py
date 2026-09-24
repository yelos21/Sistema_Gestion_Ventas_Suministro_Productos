import os 
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise RuntimeError("No se encontró DATABASE_URL en el archivo .env")
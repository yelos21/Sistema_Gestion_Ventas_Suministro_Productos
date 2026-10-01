import os 
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine
 
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, poolclass=NullPool)
 
 
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
 
 
def get_session():
    with Session(engine) as session:
        yield session

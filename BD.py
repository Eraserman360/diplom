import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

metadata = MetaData()
Base = declarative_base()

class Viewed(Base):
    __tablename__ = 'viewed'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)

db_url_object = 'postgresql://postgres:####@localhost:5432/Vkbot'  # Замените на соответствующие значения

engine = create_engine(db_url_object)
Base.metadata.create_all(engine)
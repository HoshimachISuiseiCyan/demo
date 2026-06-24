from sqlalchemy import Column, Integer, String
from app.db import Base


class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
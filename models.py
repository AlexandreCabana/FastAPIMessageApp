from sqlalchemy import Boolean, Column, Integer, String
from database import Base
class User(Base):
    __tablename__ = 'userlist'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(45),unique=False)
    password = Column(String(64),unique=False)

class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True, index=True)
    emetteur = Column(String(45), unique=False)
    destinataire = Column(String(45),unique=False)
    content = Column(String(5000),unique=False)
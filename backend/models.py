from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    options = relationship("Option", back_populates="poll")

class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    text = Column(String)

    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option")  

class Vote(Base):
    __tablename__ = "votes" 
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer)
    option_id = Column(Integer, ForeignKey("options.id"))
    created_at = Column(DateTime, default=datetime.now)

    option = relationship("Option", back_populates="votes")

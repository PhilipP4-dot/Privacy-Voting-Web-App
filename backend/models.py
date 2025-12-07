from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="open")  # "open" or "closed"

    options = relationship("Option", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="poll", cascade="all, delete-orphan")


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    text = Column(String)

    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option", cascade="all, delete-orphan")


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    option_id = Column(Integer, ForeignKey("options.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    poll = relationship("Poll", back_populates="votes")
    option = relationship("Option", back_populates="votes")


class VoteRecord(Base):
    """
    Tracks that a given (anonymous) voter has already voted in a given poll.
    This table NEVER stores what they voted for, just that they voted.
    """
    __tablename__ = "vote_records"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer)
    voter_token = Column(String)

    __table_args__ = (
        UniqueConstraint("poll_id", "voter_token", name="uq_poll_voter"),
    )

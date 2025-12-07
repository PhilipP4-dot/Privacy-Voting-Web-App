from .database import Base, engine, SessionLocal
from .models import Poll, Option

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Empty DB created with polls, options, votes, vote_records tables.")

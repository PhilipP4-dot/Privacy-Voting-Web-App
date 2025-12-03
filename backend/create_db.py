from .database import Base, engine, SessionLocal
from .models import Poll, Option

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

poll = Poll(question="Which is the best show?")
db.add(poll)
db.commit()

options = ["Bleach", "Naruto", "One Piece", "Attack on Titan", "Dragon Ball"]
for option in options:
    db.add(Option(poll_id=poll.id, text=option))

db.commit()
db.close()
print("Sample poll created in Database.")
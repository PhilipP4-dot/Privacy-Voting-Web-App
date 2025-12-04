from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Poll, Option, Vote

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/poll")
def get_poll(db: Session = Depends(get_db)):
    poll = db.query(Poll).first()
    return {
        "id": poll.id,
        "question": poll.question,
        "options": [{"id": o.id, "text": o.text} for o in poll.options]
    }

@app.post("/vote")
def submit_vote(option_id: int, db: Session = Depends(get_db)):
    option = db.query(Option).filter(Option.id == option_id).first()
    if not option:
        return {"status": "error", "message": "Invalid option"}

    vote = Vote(poll_id=option.poll_id, option_id=option.id)
    db.add(vote)
    db.commit()
    return {"status": "ok"}

@app.get("/results")
def get_results(db: Session = Depends(get_db)):
    poll = db.query(Poll).first()
    results = {}
    for opt in poll.options:
        count = db.query(Vote).filter(Vote.option_id == opt.id).count()
        results[opt.text] = count
    return results

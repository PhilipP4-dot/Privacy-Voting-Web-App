from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Poll, Option, Vote, VoteRecord
import math

EPSILON = 1.0  # must match frontend EPSILON

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PollCreatePayload(BaseModel):
    question: str


class OptionCreatePayload(BaseModel):
    poll_id: int
    text: str
    weight: float = 1.0


class VotePayload(BaseModel):
    poll_id: int
    option_id: int
    voter_token: str
    epsilon_used: float

class PollClosePayload(BaseModel):
    poll_id: int



@app.post("/create_poll")
def create_poll(payload: PollCreatePayload, db: Session = Depends(get_db)):
    poll = Poll(question=payload.question)
    db.add(poll)
    db.commit()
    db.refresh(poll)
    return {"poll_id": poll.id}


@app.post("/add_option")
def add_option(payload: OptionCreatePayload, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == payload.poll_id).first()
    if not poll:
        return {"status": "error", "message": "Poll not found"}
    option = Option(poll_id=poll.id, text=payload.text, weight=payload.weight)
    db.add(option)
    db.commit()
    return {"status": "ok"}
    
@app.post("/close_poll")
def close_poll(payload: PollClosePayload, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == payload.poll_id).first()
    if not poll:
        return {"status": "error", "message": "Poll not found"}

    poll.status = "closed"
    db.commit()

    return {"status": "ok", "message": "Poll closed"}

@app.get("/poll/{poll_id}")
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        return {"error": "Poll not found"}
    return {
        "id": poll.id,
        "question": poll.question,
        "status": poll.status,
        "options": [{"id": o.id, "text": o.text, "weight": o.weight} for o in poll.options],
    }

@app.get("/results/{poll_id}")
def get_results(poll_id: int, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        return {"error": "Poll not found"}

    # Hide results until poll is closed
    if poll.status != "closed":
        return {
            "status": "hidden",
            "message": "Results available when poll is closed"
        }

    options = poll.options
    k = len(options)
    option_ids = [opt.id for opt in options]

    # Collect all votes (each with reported ID + epsilon_used)
    votes = db.query(Vote).filter(Vote.poll_id == poll_id).all()
    n = len(votes)

    if n == 0:
        return {"status": "ok", "results": {
            opt.text: 0 for opt in options
        }}

    # Initialize debiased counts
    est = {opt.id: 0.0 for opt in options}

    # Per-vote debiasing
    for v in votes:
        eps = v.epsilon_used
        e = math.exp(eps)
        p = e / (e + k - 1)
        q = (1 - p) / (k - 1)

        for opt in options:
            if v.option_id == opt.id:  
                est[opt.id] += (1 - q) / (p - q)
            else:
                est[opt.id] += (0 - q) / (p - q)

    # Convert option IDs → text labels
    readable_results = {
        opt.text: max(0, est[opt.id])  # clip neg from noise
        for opt in options
    }

    return {
        "status": "ok",
        "results": readable_results,
        "total_reports": n
    }


@app.post("/vote")
def submit_vote(payload: VotePayload, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == payload.poll_id).first()
    if not poll:
        return {"status": "error", "message": "Poll not found"}
    if poll.status == "closed":
        return {"status": "error", "message": "Poll is closed"}
    # enforce one vote per voter per poll
    existing = db.query(VoteRecord).filter(
        VoteRecord.poll_id == payload.poll_id,
        VoteRecord.voter_token == payload.voter_token,
    ).first()

    if existing:
        return {"status": "error", "message": "Already voted"}

    # record that this voter has voted in this poll
    record = VoteRecord(poll_id=payload.poll_id, voter_token=payload.voter_token)
    db.add(record)

    # Store the *reported* vote + effective epsilon
    vote = Vote(
        poll_id=payload.poll_id,
        option_id=payload.option_id,    # noisy version!
        epsilon_used=payload.epsilon_used
    )
    db.add(vote)

    db.commit()
    return {"status": "ok"}

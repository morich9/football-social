from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from fastapi.security import OAuth2PasswordRequestForm  
import hashlib

from database import engine, Base, SessionLocal
import models
import schemas
import auth
import football_api
import os
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "changeme123")

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="Static", html=True), name="static")

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/")
def read_root():
    return {"message": "سلام! سرور فوتبالی من روشنه ⚽"}

@app.post("/users/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="این یوزرنیم یا ایمیل قبلاً ثبت شده")
    db.refresh(new_user)
    return new_user

@app.post("/users/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or user.password_hash != hash_password(form_data.password):
        raise HTTPException(status_code=401, detail="یوزرنیم یا پسورد اشتباهه")
    token = auth.create_access_token({"sub": user.username, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/matches", response_model=schemas.MatchOut)
def create_match(match: schemas.MatchCreate, admin_secret: str, db: Session = Depends(get_db)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="دسترسی نداری")

    new_match = models.Match(home_team=match.home_team, away_team=match.away_team)
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    return new_match

@app.post("/matches/sync")
def sync_matches(admin_secret: str, db: Session = Depends(get_db)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="دسترسی نداری")

    data = football_api.get_scheduled_matches()
    added = 0
    for m in data.get("matches", []):
        exists = db.query(models.Match).filter(models.Match.external_id == m["id"]).first()
        if exists:
            continue
        new_match = models.Match(
            external_id=m["id"],
            home_team=m["homeTeam"]["name"],
            away_team=m["awayTeam"]["name"],
            status="scheduled"
        )
        db.add(new_match)
        added += 1
    db.commit()
    return {"added": added}

@app.get("/matches", response_model=List[schemas.MatchOut])
def list_matches(db: Session = Depends(get_db)):
    return db.query(models.Match).all()

@app.post("/matches/{match_id}/comments", response_model=schemas.CommentOut)
def add_comment(match_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="بازی پیدا نشد")

    new_comment = models.Comment(
        match_id=match_id,
        user_id=current_user.id,
        minute=comment.minute,
        content=comment.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@app.get("/matches/{match_id}/comments", response_model=List[schemas.CommentOut])
def get_comments(match_id: int, db: Session = Depends(get_db)):
    return db.query(models.Comment).filter(models.Comment.match_id == match_id).order_by(models.Comment.minute).all()

@app.post("/comments/{comment_id}/reply", response_model=schemas.CommentOut)
def reply_to_comment(comment_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    parent = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent comment not found")

    new_reply = models.Comment(
        match_id=parent.match_id,
        user_id=current_user.id,
        parent_id=comment_id,
        minute=parent.minute,
        content=comment.content
    )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    return new_reply

@app.get("/comments/{comment_id}/replies", response_model=List[schemas.CommentOut])
def get_replies(comment_id: int, db: Session = Depends(get_db)):
    return db.query(models.Comment).filter(models.Comment.parent_id == comment_id).all()

@app.post("/comments/{comment_id}/reactions", response_model=schemas.ReactionOut)
def add_reaction(comment_id: int, reaction: schemas.ReactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    new_reaction = models.Reaction(comment_id=comment_id, user_id=current_user.id, type=reaction.type)
    db.add(new_reaction)
    db.commit()
    db.refresh(new_reaction)
    return new_reaction

@app.get("/comments/{comment_id}/reactions", response_model=List[schemas.ReactionOut])
def get_reactions(comment_id: int, db: Session = Depends(get_db)):
    return db.query(models.Reaction).filter(models.Reaction.comment_id == comment_id).all()

@app.put("/users/me", response_model=schemas.UserOut)
def update_profile(profile: schemas.ProfileUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if profile.favorite_team is not None:
        current_user.favorite_team = profile.favorite_team
    if profile.favorite_player is not None:
        current_user.favorite_player = profile.favorite_player
    if profile.bio is not None:
        current_user.bio = profile.bio

    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/live-matches")
def live_matches():
    return football_api.get_live_matches()

@app.get("/scheduled-matches")
def scheduled_matches():
    return football_api.get_scheduled_matches()
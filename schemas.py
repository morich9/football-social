from pydantic import BaseModel, EmailStr
import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    favorite_team: str | None
    favorite_player: str | None
    bio: str | None

    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    favorite_team: str | None = None
    favorite_player: str | None = None
    bio: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class MatchCreate(BaseModel):
    home_team: str
    away_team: str

class MatchOut(BaseModel):
    id: int
    home_team: str
    away_team: str
    status: str

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    minute: int
    content: str
    parent_id: int | None = None

class CommentOut(BaseModel):
    id: int
    minute: int
    content: str
    user_id: int
    parent_id: int | None

    class Config:
        from_attributes = True

class ReactionCreate(BaseModel):
    type: str = "like"

class ReactionOut(BaseModel):
    id: int
    comment_id: int
    user_id: int
    type: str

    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    role: str # 'child', 'parent', 'teacher', 'therapist'
    students: Optional[List[str]] = None

class UserCreate(User):
    password: str

class UserInDB(User):
    hashed_password: str

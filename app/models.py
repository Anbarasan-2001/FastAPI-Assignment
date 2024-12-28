from pydantic import BaseModel, EmailStr
from datetime import datetime

class User(BaseModel):
    user_id       : str
    user_name     : str
    user_email    : EmailStr
    mobile_number : str
    password      : str
    created_on    : datetime
    last_update   : datetime

class NoteCreate(BaseModel):
    title   : str
    content : str

    class Config:
        orm_mode = True

class Note(BaseModel):
    note_id     : str
    title       : str
    content     : str
    user_email  : str
    created_on  : datetime
    last_update : datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.database import db
from app.models import User, NoteCreate, Note
from app.auth import create_access_token, verify_password, hash_password, decode_token
from datetime import datetime, timedelta
from bson import ObjectId

router        = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS   = 30


# Register Route
@router.post("/register/")
async def register(user: User):
    existing_user = await db.users.find_one({"user_email": user.user_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password          = hash_password(user.password)
    user_data                = user.dict()
    user_data["password"]    = hashed_password
    user_data["created_on"]  = datetime.utcnow()
    user_data["last_update"] = datetime.utcnow()

    await db.users.insert_one(user_data)
    return {"message": "User registered successfully"}


# Login Route
@router.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"user_email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user["user_email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": user["user_email"]},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Create Note
@router.post("/notes/", response_model=Note)
async def create_note(note: NoteCreate, token: str = Depends(oauth2_scheme)):
    user_email = decode_token(token)

    note_data = {
        "note_id"     : str(ObjectId()),
        "title"       : note.title,
        "content"     : note.content,
        "user_email"  : user_email,
        "created_on"  : datetime.utcnow(),
        "last_update" : datetime.utcnow(),
    }

    await db.notes.insert_one(note_data)
    return Note(**note_data)


# Get Notes
@router.get("/notes/", response_model=list[Note])
async def get_notes(token: str = Depends(oauth2_scheme)):
    user_email = decode_token(token)

    notes_cursor = db.notes.find({"user_email": user_email})
    notes        = await notes_cursor.to_list(length=100)
    return [Note(**note) for note in notes]


# Update Note
@router.put("/notes/{note_id}")
async def update_note(note_id: str, note: NoteCreate, token: str = Depends(oauth2_scheme)):
    user_email = decode_token(token)

    result = await db.notes.update_one(
        {"note_id": note_id, "user_email": user_email},
        {
            "$set": {
                "title"       : note.title,
                "content"     : note.content,
                "last_update" : datetime.utcnow(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    return {"message": "Note updated successfully"}


# Delete Note
@router.delete("/notes/{note_id}")
async def delete_note(note_id: str, token: str = Depends(oauth2_scheme)):
    user_email = decode_token(token)

    result = await db.notes.delete_one({"note_id": note_id, "user_email": user_email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    return {"message": "Note deleted successfully"}


# Check Token Validity
@router.get("/check-token/")
async def check_token_expiration(token: str = Depends(oauth2_scheme)):
    try:
        decode_token(token)
        return {"status": "valid", "message": "The token is still valid"}
    except HTTPException:
        return {"status": "expired", "message": "The token has expired"}


# Refresh Access Token
@router.post("/refresh-token/")
async def refresh_access_token(refresh_token: str):
    try:
        user_email       = decode_token(refresh_token)
        new_access_token = create_access_token(
            data={"sub": user_email}, 
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


# Logout
@router.post("/logout/")
async def logout():
    return {"message": "Logged out successfully (client-side must delete tokens)"}
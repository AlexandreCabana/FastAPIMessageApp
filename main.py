from typing import Annotated, Optional
import hashlib
from urllib import response

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
models.Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependacy = Depends(get_db)
class User(BaseModel):
    id: int
    username: str
    password: str

    @classmethod
    def as_form(cls, username : Annotated[str, Form()], password: Annotated[str, Form()], db =db_dependacy):
        if len([i for i in db.query(models.User).all()]) == 0:
            id = 1
        else:
            id = db.query(models.User).order_by(models.User.id.desc()).first().id + 1
        return cls(id=id,username=username, password=hashlib.sha256(password.encode()).hexdigest())
class Message(BaseModel):
    id: int
    emetteur: str
    destinataire: str
    content: str

    @classmethod
    def as_form(cls, emetteur : Annotated[str, Form()],destinataire : Annotated[str, Form()], content: Annotated[str, Form()], db =db_dependacy):
        if len([i for i in db.query(models.Message).all()]) == 0:
            id = 1
        else:
            id = db.query(models.Message).order_by(models.Message.id.desc()).first().id + 1
        return cls(id=id,emetteur=emetteur, destinataire=destinataire, content=content)
app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.mount("/image", StaticFiles(directory="image"), name="image")

templates = Jinja2Templates(directory="templates")
@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/createAccount")
async def createAccount(request: Request):
    return templates.TemplateResponse("createAccount.html", {"request": request})
@app.post("/createAccount")
async def createAccount(request: Request, user: User = Depends(User.as_form), db=db_dependacy):
    if not db.query(db.query(models.User).filter(models.User.username == user.username).exists()).scalar():
        dbUser = models.User(**user.dict())
        db.add(dbUser)
        db.commit()
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/sendMessage")
async def sendMessage(request: Request, username: Annotated[str, Form()], message: Annotated[str, Form()], loginUsername: Annotated[str | None, Cookie()] = None, db=db_dependacy):
    if len([i for i in db.query(models.Message).all()]) == 0:
        id = 1
    else:
        id = db.query(models.Message).order_by(models.Message.id.desc()).first().id + 1
    dbMessage = models.Message(id=id,emetteur=loginUsername, destinataire=username, content=message)
    db.add(dbMessage)
    db.commit()
    return goToDashboard(request, db=db, loginUsername=loginUsername)
@app.post("/login")
async def login(request: Request, username : Annotated[str, Form()], password: Annotated[str, Form()], db=db_dependacy):
    if not db.query(db.query(models.User).filter(models.User.username == username).exists()).scalar():
        return templates.TemplateResponse("createAccount.html", {"request": request})
    elif db.query(models.User).filter(models.User.username == username).first().password != hashlib.sha256(password.encode()).hexdigest():
        raise HTTPException(status_code=400, detail="Wrong password")
    response = goToDashboard(request, db=db, loginUsername=username)
    response.set_cookie("loginUsername", username)
    return response

@app.get("/dashboard")
def goToDashboard(request: Request, db, loginUsername:str):
    listMessage = db.query(models.Message).filter(models.Message.destinataire == loginUsername).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "listMessage": listMessage})

@app.get("/logout")
def logout(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request})
    response.set_cookie("loginUsername", "")
    return response

@app.get("/deleteMessage/{id}")
def deleteMessage(request: Request, id: int, loginUsername: Annotated[str | None, Cookie()] = None, db=db_dependacy):
    messageToDelete: Message = db.query(models.Message).filter(models.Message.id == id).first()
    if messageToDelete.destinataire.lower() == loginUsername:
        db.delete(messageToDelete)
        db.commit()
    return goToDashboard(request, db, loginUsername)

@app.get("/")
def defaultPage(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
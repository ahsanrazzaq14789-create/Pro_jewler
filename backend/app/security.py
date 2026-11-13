import os
from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User,Membership
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth=OAuth2PasswordBearer(tokenUrl="/auth/login")
SECRET=os.getenv("SECRET_KEY","development-only-change-me")
ALG="HS256"
def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def make_token(user):
    return jwt.encode({"sub":str(user.id),"exp":datetime.now(timezone.utc)+timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES","720")))},SECRET,algorithm=ALG)
def current_user(token:str=Depends(oauth),db:Session=Depends(get_db)):
    err=HTTPException(401,"Invalid or expired login",headers={"WWW-Authenticate":"Bearer"})
    try: uid=int(jwt.decode(token,SECRET,algorithms=[ALG])["sub"])
    except Exception: raise err
    u=db.get(User,uid)
    if not u or not u.is_active: raise err
    return u
def shop_access(shop_id:int,user:User,db:Session,roles=None):
    if user.role=="super_admin": return
    m=db.query(Membership).filter_by(user_id=user.id,shop_id=shop_id).first()
    if not m or (roles and m.role not in roles): raise HTTPException(403,"No access to this shop")
    return m
def require_super(user:User):
    if user.role!="super_admin": raise HTTPException(403,"Super Admin only")

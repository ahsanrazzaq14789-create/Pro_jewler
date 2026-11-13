import os, uuid, json, csv, io
from fastapi import FastAPI,Depends,HTTPException,Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .database import Base,engine,get_db,SessionLocal
from .models import User,Shop,Membership,BusinessRecord,AuditLog
from .schemas import LoginIn,RegisterIn,ShopIn,RecordIn
from .security import hash_password,verify_password,make_token,current_user,shop_access,require_super

app=FastAPI(title="Gold & Silver Business API",version="1.0.0",description="Multi-shop jewellery business management backend")
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def bootstrap():
    db=SessionLocal()
    try:
        email=os.getenv("BOOTSTRAP_ADMIN_EMAIL","")
        password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD","")
        if email and password and not db.query(User).filter_by(email=email).first():
            db.add(User(email=email,password_hash=hash_password(password),full_name="System Super Admin",role="super_admin"))
            db.commit()
    finally: db.close()

@app.get("/health")
def health(): return {"status":"ok","service":"gold-silver-api"}

@app.post("/auth/register")
def register(x:RegisterIn,db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=x.email.lower()).first(): raise HTTPException(409,"Email already registered")
    u=User(email=x.email.lower(),password_hash=hash_password(x.password),full_name=x.full_name,role="shop_admin")
    db.add(u);db.flush()
    s=Shop(name=x.shop_name,owner_name=x.full_name,phone=x.phone);db.add(s);db.flush()
    db.add(Membership(user_id=u.id,shop_id=s.id,role="shop_admin"));db.commit()
    return {"access_token":make_token(u),"token_type":"bearer","user_id":u.id,"shop_id":s.id}

@app.post("/auth/login")
def login(x:LoginIn,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=x.email.lower()).first()
    if not u or not u.is_active or not verify_password(x.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"access_token":make_token(u),"token_type":"bearer","user":{"id":u.id,"email":u.email,"name":u.full_name,"role":u.role}}

@app.get("/auth/me")
def me(u:User=Depends(current_user)):
    return {"id":u.id,"email":u.email,"name":u.full_name,"role":u.role}

@app.get("/shops")
def shops(db:Session=Depends(get_db),u:User=Depends(current_user)):
    if u.role=="super_admin": items=db.query(Shop).all()
    else:
        ids=[m.shop_id for m in db.query(Membership).filter_by(user_id=u.id).all()]
        items=db.query(Shop).filter(Shop.id.in_(ids)).all()
    return [{"id":s.id,"name":s.name,"owner_name":s.owner_name,"phone":s.phone,"address":s.address,"currency":s.currency} for s in items]

@app.post("/shops")
def create_shop(x:ShopIn,db:Session=Depends(get_db),u:User=Depends(current_user)):
    if u.role not in ("super_admin","shop_admin"): raise HTTPException(403,"Shop admin only")
    s=Shop(**x.model_dump());db.add(s);db.flush()
    db.add(Membership(user_id=u.id,shop_id=s.id,role="shop_admin"));db.commit()
    return {"id":s.id,"name":s.name}

@app.patch("/shops/{shop_id}")
def update_shop(shop_id:int,x:ShopIn,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db,["shop_admin"])
    s=db.get(Shop,shop_id)
    if not s: raise HTTPException(404,"Shop not found")
    for k,v in x.model_dump().items(): setattr(s,k,v)
    db.commit();return {"ok":True}

@app.get("/shops/{shop_id}/members")
def members(shop_id:int,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db,["shop_admin"])
    rows=db.query(Membership,User).join(User,User.id==Membership.user_id).filter(Membership.shop_id==shop_id).all()
    return [{"user_id":usr.id,"email":usr.email,"name":usr.full_name,"role":m.role} for m,usr in rows]

@app.post("/shops/{shop_id}/members")
def add_member(shop_id:int,email:str,role:str="cashier",db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db,["shop_admin"])
    if role not in ["shop_admin","manager","cashier","accountant","worker"]: raise HTTPException(400,"Invalid role")
    target=db.query(User).filter_by(email=email.lower()).first()
    if not target: raise HTTPException(404,"Create user account first")
    m=db.query(Membership).filter_by(user_id=target.id,shop_id=shop_id).first()
    if m: m.role=role
    else: db.add(Membership(user_id=target.id,shop_id=shop_id,role=role))
    db.commit();return {"ok":True}

@app.get("/shops/{shop_id}/records")
def list_records(shop_id:int,module:str|None=None,q:str="",since:str|None=None,limit:int=500,offset:int=0,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db)
    query=db.query(BusinessRecord).filter_by(shop_id=shop_id)
    if module: query=query.filter_by(module=module)
    if q: query=query.filter(or_(BusinessRecord.title.ilike(f"%{q}%"),BusinessRecord.party.ilike(f"%{q}%"),BusinessRecord.reference.ilike(f"%{q}%"),BusinessRecord.details.ilike(f"%{q}%")))
    if since: query=query.filter(BusinessRecord.updated_at>since)
    return query.order_by(BusinessRecord.updated_at.desc()).offset(offset).limit(min(limit,2000)).all()

@app.put("/shops/{shop_id}/records")
def upsert_record(shop_id:int,x:RecordIn,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db)
    if x.amount<0 or x.paid<0 or x.weight<0 or x.purity<0: raise HTTPException(400,"Negative values are not allowed")
    r=db.get(BusinessRecord,x.id)
    if r and r.shop_id!=shop_id: raise HTTPException(409,"Record belongs to another shop")
    if r and x.version<r.version: raise HTTPException(409,"Stale record version; refresh before editing")
    data=x.model_dump()
    if r:
        for k,v in data.items():
            if k!="id" and k!="version": setattr(r,k,v)
        r.version+=1
    else:
        r=BusinessRecord(**data,shop_id=shop_id);db.add(r)
    db.add(AuditLog(shop_id=shop_id,user_id=u.id,action="upsert_record",entity_id=x.id,detail=x.module))
    db.commit();db.refresh(r);return r

@app.delete("/shops/{shop_id}/records/{record_id}")
def delete_record(shop_id:int,record_id:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db)
    r=db.get(BusinessRecord,record_id)
    if not r or r.shop_id!=shop_id: raise HTTPException(404,"Record not found")
    r.deleted=True;r.version+=1
    db.add(AuditLog(shop_id=shop_id,user_id=u.id,action="delete_record",entity_id=record_id,detail=r.module))
    db.commit();return {"ok":True}

@app.get("/shops/{shop_id}/summary")
def summary(shop_id:int,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db)
    rows=db.query(BusinessRecord).filter_by(shop_id=shop_id,deleted=False).all()
    out={}
    for r in rows:
        m=out.setdefault(r.module,{"count":0,"amount":0.0,"paid":0.0,"balance":0.0,"weight":0.0})
        m["count"]+=1;m["amount"]+=r.amount;m["paid"]+=r.paid;m["balance"]+=r.balance;m["weight"]+=r.weight
    return out

@app.get("/admin/shops")
def admin_shops(db:Session=Depends(get_db),u:User=Depends(current_user)):
    require_super(u)
    return [{"id":s.id,"name":s.name,"active":s.is_active,"phone":s.phone} for s in db.query(Shop).all()]

@app.patch("/admin/shops/{shop_id}/status")
def admin_shop_status(shop_id:int,active:bool,db:Session=Depends(get_db),u:User=Depends(current_user)):
    require_super(u);s=db.get(Shop,shop_id)
    if not s: raise HTTPException(404,"Shop not found")
    s.is_active=active;db.commit();return {"ok":True,"active":active}

@app.get("/shops/{shop_id}/backup")
def backup(shop_id:int,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db,["shop_admin"])
    s=db.get(Shop,shop_id)
    rows=db.query(BusinessRecord).filter_by(shop_id=shop_id).all()
    payload={"shop":{"id":s.id,"name":s.name,"owner_name":s.owner_name,"phone":s.phone,"address":s.address,"currency":s.currency},
      "records":[{c.name:getattr(r,c.name) for c in BusinessRecord.__table__.columns} for r in rows]}
    return payload

@app.get("/shops/{shop_id}/audit")
def audit(shop_id:int,db:Session=Depends(get_db),u:User=Depends(current_user)):
    shop_access(shop_id,u,db,["shop_admin"])
    return db.query(AuditLog).filter_by(shop_id=shop_id).order_by(AuditLog.created_at.desc()).limit(1000).all()

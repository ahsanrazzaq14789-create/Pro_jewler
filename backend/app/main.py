import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .database import Base, engine, get_db, SessionLocal
from .models import (
    User, Shop, Membership, BusinessRecord, AuditLog,
    Account, JournalEntry, JournalLine
)
from .schemas import LoginIn, RegisterIn, ShopIn, RecordIn
from .security import (
    hash_password, verify_password, make_token,
    current_user, shop_access, require_super
)

app = FastAPI(
    title="Gold & Silver Business API",
    version="2.0.0",
    description="Jewellery business management backend"
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def bootstrap():
    db = SessionLocal()
    try:
        email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").lower()
        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

        if email and password:
            user = db.query(User).filter_by(email=email).first()
            if not user:
                db.add(User(
                    email=email,
                    password_hash=hash_password(password),
                    full_name="System Super Admin",
                    role="super_admin"
                ))
                db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "gold-silver-api"}


@app.post("/auth/register")
def register(x: RegisterIn, db: Session = Depends(get_db)):
    email = x.email.lower()

    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(x.password),
        full_name=x.full_name,
        role="shop_admin"
    )
    db.add(user)
    db.flush()

    shop = Shop(
        name=x.shop_name,
        owner_name=x.full_name,
        phone=x.phone
    )
    db.add(shop)
    db.flush()

    db.add(Membership(
        user_id=user.id,
        shop_id=shop.id,
        role="shop_admin"
    ))

    db.commit()

    return {
        "access_token": make_token(user),
        "token_type": "bearer",
        "user_id": user.id,
        "shop_id": shop.id
    }


@app.post("/auth/login")
def login(x: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=x.email.lower()).first()

    if (
        not user
        or not user.is_active
        or not verify_password(x.password, user.password_hash)
    ):
        raise HTTPException(401, "Incorrect email or password")

    return {
        "access_token": make_token(user),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role
        }
    }


@app.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.full_name,
        "role": user.role
    }


@app.get("/shops")
def shops(db: Session = Depends(get_db),
          user: User = Depends(current_user)):

    if user.role == "super_admin":
        items = db.query(Shop).all()
    else:
        ids = [
            m.shop_id
            for m in db.query(Membership).filter_by(user_id=user.id).all()
        ]
        items = db.query(Shop).filter(Shop.id.in_(ids)).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "owner_name": s.owner_name,
            "phone": s.phone,
            "address": s.address,
            "currency": s.currency
        }
        for s in items
    ]


@app.post("/shops")
def create_shop(x: ShopIn, db: Session = Depends(get_db),
                user: User = Depends(current_user)):

    if user.role not in ("super_admin", "shop_admin"):
        raise HTTPException(403, "Shop admin only")

    shop = Shop(**x.model_dump())
    db.add(shop)
    db.flush()

    db.add(Membership(
        user_id=user.id,
        shop_id=shop.id,
        role="shop_admin"
    ))

    db.commit()
    return {"id": shop.id, "name": shop.name}


@app.patch("/shops/{shop_id}")
def update_shop(shop_id: int, x: ShopIn,
                db: Session = Depends(get_db),
                user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin"])

    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(404, "Shop not found")

    for key, value in x.model_dump().items():
        setattr(shop, key, value)

    db.commit()
    return {"ok": True}


@app.get("/shops/{shop_id}/members")
def members(shop_id: int, db: Session = Depends(get_db),
            user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin"])

    rows = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.shop_id == shop_id)
        .all()
    )

    return [
        {
            "user_id": usr.id,
            "email": usr.email,
            "name": usr.full_name,
            "role": membership.role
        }
        for membership, usr in rows
    ]


@app.post("/shops/{shop_id}/members")
def add_member(shop_id: int, email: str,
               role: str = "cashier",
               db: Session = Depends(get_db),
               user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin"])

    allowed = [
        "shop_admin", "manager", "cashier",
        "accountant", "worker"
    ]

    if role not in allowed:
        raise HTTPException(400, "Invalid role")

    target = db.query(User).filter_by(email=email.lower()).first()

    if not target:
        raise HTTPException(404, "Create user account first")

    membership = db.query(Membership).filter_by(
        user_id=target.id,
        shop_id=shop_id
    ).first()

    if membership:
        membership.role = role
    else:
        db.add(Membership(
            user_id=target.id,
            shop_id=shop_id,
            role=role
        ))

    db.commit()
    return {"ok": True}


@app.get("/shops/{shop_id}/records")
def list_records(
    shop_id: int,
    module: str | None = None,
    q: str = "",
    limit: int = 500,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    shop_access(shop_id, user, db)

    query = db.query(BusinessRecord).filter_by(
        shop_id=shop_id,
        deleted=False
    )

    if module:
        query = query.filter_by(module=module)

    if q:
        query = query.filter(or_(
            BusinessRecord.title.ilike(f"%{q}%"),
            BusinessRecord.party.ilike(f"%{q}%"),
            BusinessRecord.reference.ilike(f"%{q}%"),
            BusinessRecord.details.ilike(f"%{q}%")
        ))

    return (
        query.order_by(BusinessRecord.updated_at.desc())
        .offset(offset)
        .limit(min(limit, 2000))
        .all()
    )


@app.put("/shops/{shop_id}/records")
def upsert_record(shop_id: int, x: RecordIn,
                  db: Session = Depends(get_db),
                  user: User = Depends(current_user)):

    shop_access(shop_id, user, db)

    if min(x.amount, x.paid, x.weight, x.purity) < 0:
        raise HTTPException(400, "Negative values are not allowed")

    record = db.get(BusinessRecord, x.id)

    if record and record.shop_id != shop_id:
        raise HTTPException(409, "Record belongs to another shop")

    if record and x.version < record.version:
        raise HTTPException(409, "Stale record version")

    data = x.model_dump()

    if record:
        for key, value in data.items():
            if key not in ("id", "version"):
                setattr(record, key, value)
        record.version += 1
    else:
        record = BusinessRecord(**data, shop_id=shop_id)
        db.add(record)

    db.add(AuditLog(
        shop_id=shop_id,
        user_id=user.id,
        action="upsert_record",
        entity_id=x.id,
        detail=x.module
    ))

    db.commit()
    db.refresh(record)
    return record


@app.delete("/shops/{shop_id}/records/{record_id}")
def delete_record(shop_id: int, record_id: str,
                  db: Session = Depends(get_db),
                  user: User = Depends(current_user)):

    shop_access(shop_id, user, db)

    record = db.get(BusinessRecord, record_id)

    if not record or record.shop_id != shop_id:
        raise HTTPException(404, "Record not found")

    record.deleted = True
    record.version += 1

    db.add(AuditLog(
        shop_id=shop_id,
        user_id=user.id,
        action="delete_record",
        entity_id=record_id,
        detail=record.module
    ))

    db.commit()
    return {"ok": True}


@app.get("/shops/{shop_id}/summary")
def summary(shop_id: int, db: Session = Depends(get_db),
            user: User = Depends(current_user)):

    shop_access(shop_id, user, db)

    rows = db.query(BusinessRecord).filter_by(
        shop_id=shop_id,
        deleted=False
    ).all()

    output = {}

    for record in rows:
        item = output.setdefault(record.module, {
            "count": 0,
            "amount": 0.0,
            "paid": 0.0,
            "balance": 0.0,
            "weight": 0.0
        })

        item["count"] += 1
        item["amount"] += record.amount
        item["paid"] += record.paid
        item["balance"] += record.balance
        item["weight"] += record.weight

    return output


@app.get("/admin/shops")
def admin_shops(db: Session = Depends(get_db),
                user: User = Depends(current_user)):

    require_super(user)

    return [
        {
            "id": s.id,
            "name": s.name,
            "active": s.is_active,
            "phone": s.phone
        }
        for s in db.query(Shop).all()
    ]


@app.patch("/admin/shops/{shop_id}/status")
def admin_shop_status(shop_id: int, active: bool,
                      db: Session = Depends(get_db),
                      user: User = Depends(current_user)):

    require_super(user)

    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(404, "Shop not found")

    shop.is_active = active
    db.commit()

    return {"ok": True, "active": active}


@app.get("/shops/{shop_id}/backup")
def backup(shop_id: int, db: Session = Depends(get_db),
           user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin"])

    shop = db.get(Shop, shop_id)

    rows = db.query(BusinessRecord).filter_by(
        shop_id=shop_id
    ).all()

    return {
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "owner_name": shop.owner_name,
            "phone": shop.phone,
            "address": shop.address,
            "currency": shop.currency
        },
        "records": [
            {
                column.name: getattr(row, column.name)
                for column in BusinessRecord.__table__.columns
            }
            for row in rows
        ]
    }


@app.get("/shops/{shop_id}/audit")
def audit(shop_id: int, db: Session = Depends(get_db),
          user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin"])

    return (
        db.query(AuditLog)
        .filter_by(shop_id=shop_id)
        .order_by(AuditLog.created_at.desc())
        .limit(1000)
        .all()
    )


# ACCOUNTING

DEFAULT_ACCOUNTS = [
    ("1000", "Cash in Hand", "asset"),
    ("1010", "Bank", "asset"),
    ("1100", "Accounts Receivable", "asset"),
    ("1200", "Inventory", "asset"),
    ("2000", "Accounts Payable", "liability"),
    ("2100", "Customer Advances", "liability"),
    ("3000", "Owner Capital", "equity"),
    ("3100", "Retained Earnings", "equity"),
    ("4000", "Sales Revenue", "income"),
    ("4100", "Making Charges Income", "income"),
    ("5000", "Cost of Goods Sold", "expense"),
    ("5100", "Shop Expenses", "expense")
]


@app.post("/shops/{shop_id}/accounting/setup")
def accounting_setup(shop_id: int,
                     db: Session = Depends(get_db),
                     user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin", "accountant"])

    for code, name, account_type in DEFAULT_ACCOUNTS:
        exists = db.query(Account).filter_by(
            shop_id=shop_id,
            code=code
        ).first()

        if not exists:
            db.add(Account(
                shop_id=shop_id,
                code=code,
                name=name,
                account_type=account_type
            ))

    db.commit()

    return {
        "ok": True,
        "accounts": db.query(Account).filter_by(
            shop_id=shop_id
        ).count()
    }


@app.get("/shops/{shop_id}/accounting/accounts")
def accounting_accounts(shop_id: int,
                        db: Session = Depends(get_db),
                        user: User = Depends(current_user)):

    shop_access(shop_id, user, db)

    return (
        db.query(Account)
        .filter_by(shop_id=shop_id)
        .order_by(Account.code)
        .all()
    )


@app.post("/shops/{shop_id}/accounting/accounts")
def create_account(shop_id: int, code: str, name: str,
                   account_type: str,
                   db: Session = Depends(get_db),
                   user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin", "accountant"])

    allowed = {"asset", "liability", "equity", "income", "expense"}

    if account_type not in allowed:
        raise HTTPException(400, "Invalid account type")

    code = code.strip()
    name = name.strip()

    if not code or not name:
        raise HTTPException(400, "Code and name are required")

    if db.query(Account).filter_by(
        shop_id=shop_id,
        code=code
    ).first():
        raise HTTPException(409, "Account code already exists")

    account = Account(
        shop_id=shop_id,
        code=code,
        name=name,
        account_type=account_type
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@app.post("/shops/{shop_id}/accounting/journals")
def create_journal(shop_id: int, payload: dict,
                   db: Session = Depends(get_db),
                   user: User = Depends(current_user)):

    shop_access(shop_id, user, db, ["shop_admin", "accountant"])

    lines = payload.get("lines", [])

    if len(lines) < 2:
        raise HTTPException(400, "At least two journal lines are required")

    try:
        total_debit = round(
            sum(float(line.get("debit", 0)) for line in lines), 2
        )
        total_credit = round(
            sum(float(line.get("credit", 0)) for line in lines), 2
        )
    except (TypeError, ValueError):
        raise HTTPException(400, "Invalid debit or credit amount")

    if total_debit <= 0 or total_debit != total_credit:
        raise HTTPException(400, "Journal debit and credit must balance")

    entry = JournalEntry(
        shop_id=shop_id,
        reference=str(payload.get("reference", ""))[:100],
        narration=str(payload.get("narration", "")),
        created_by=user.id
    )

    db.add(entry)
    db.flush()

    for item in lines:
        try:
            debit = round(float(item.get("debit", 0)), 2)
            credit = round(float(item.get("credit", 0)), 2)
            account_id = int(item.get("account_id", 0))
        except (TypeError, ValueError):
            db.rollback()
            raise HTTPException(400, "Invalid journal line")

        if (
            debit < 0 or credit < 0
            or (debit > 0 and credit > 0)
            or (debit == 0 and credit == 0)
        ):
            db.rollback()
            raise HTTPException(
                400,
                "Each line needs either debit or credit"
            )

        account = db.get(Account, account_id)

        if (
            not account
            or account.shop_id != shop_id
            or not account.is_active
        ):
            db.rollback()
            raise HTTPException(400, "Invalid account")

        db.add(JournalLine(
            entry_id=entry.id,
            account_id=account.id,
            debit=debit,
            credit=credit,
            description=str(item.get("description", ""))[:240]
        ))

    db.add(AuditLog(
        shop_id=shop_id,
        user_id=user.id,
        action="create_journal",
        entity_id=str(entry.id),
        detail=entry.reference
    ))

    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "reference": entry.reference,
        "debit": total_debit,
        "credit": total_credit,
        "status": "posted"
    }


@app.get("/shops/{shop_id}/accounting/trial-balance")
def trial_balance(shop_id: int,
                  db: Session = Depends(get_db),
                  user: User = Depends(current_user)):

    shop_access(shop_id, user, db)

    accounts = (
        db.query(Account)
        .filter_by(shop_id=shop_id)
        .order_by(Account.code)
        .all()
    )

    result = []
    grand_debit = 0.0
    grand_credit = 0.0

    for account in accounts:
        rows = (
            db.query(JournalLine)
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .filter(
                JournalEntry.shop_id == shop_id,
                JournalLine.account_id == account.id
            )
            .all()
        )

        net = round(sum(
            row.debit - row.credit for row in rows
        ), 2)

        debit = max(net, 0)
        credit = max(-net, 0)

        grand_debit += debit
        grand_credit += credit

        result.append({
            "account_id": account.id,
            "code": account.code,
            "name": account.name,
            "type": account.account_type,
            "debit": debit,
            "credit": credit
        })

    return {
        "accounts": result,
        "total_debit": round(grand_debit, 2),
        "total_credit": round(grand_credit, 2),
        "balanced": round(grand_debit, 2) == round(grand_credit, 2)
    }


@app.get("/shops/{shop_id}/accounting/profit-loss")
def profit_loss(shop_id: int,
                db: Session = Depends(get_db),
                user: User = Depends(current_user)):

    shop_access(shop_id, user, db)

    accounts = (
        db.query(Account)
        .filter(
            Account.shop_id == shop_id,
            Account.account_type.in_(["income", "expense"])
        )
        .all()
    )

    income = 0.0
    expenses = 0.0
    details = []

    for account in accounts:
        rows = (
            db.query(JournalLine)
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .filter(
                JournalEntry.shop_id == shop_id,
                JournalLine.account_id == account.id
            )
            .all()
        )

        if account.account_type == "income":
            amount = round(sum(
                row.credit - row.debit for row in rows
            ), 2)
            income += amount
        else:
            amount = round(sum(
                row.debit - row.credit for row in rows
            ), 2)
            expenses += amount

        details.append({
            "code": account.code,
            "name": account.name,
            "type": account.account_type,
            "amount": amount
        })

    return {
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "net_profit": round(income - expenses, 2),
        "details": details
                   }

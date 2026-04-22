import fastapi
import fastapi.middleware
import fastapi.middleware.cors
import pydantic
from typing import Optional
import sqlite3
import datetime
import uuid
import bcrypt
import jwt
import os
import faker

fake = faker.Faker()
SECRET_KEY = os.getenv("secret_key")
ALGORITHM = os.getenv("algorithm")

def encrypt_password(password: str):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

app = fastapi.FastAPI()

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_token(user_id: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, display_name, organizations, id, Email, super_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        payload = {
            "user_id": user_id,
            "username": user[0],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "display_name": user[1],
            "organizations": user[2],
            "email": user[4],
            "is_super_admin": user[5]
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    else:
        fastapi.HTTPException(status_code=404, detail="User not found")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise fastapi.HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise fastapi.HTTPException(status_code=401, detail="Invalid token")

class User(pydantic.BaseModel):
    username: str
    display_name: str
    password: str
    email: str

class LoginRequest(pydantic.BaseModel):
    username: str
    password: str
class Organization(pydantic.BaseModel):
    name: str
    owner_id: str
    super_admin_token: str

class Transaction(pydantic.BaseModel):
    title: str
    sender_bank_account_id: str
    sender_user_id: str
    receiver_bank_account_id: str
    amount: float

class Card(pydantic.BaseModel):
    card_name: str
    card_holder_id: str
    bank_account_id: str
    spending_limit: float

class CardTransaction(pydantic.BaseModel):
    card_number: str
    cvv: str
    amount: float
    description: Optional[str] = None

@app.post("/register/")
def add_user(user: User):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO users (id, username, display_name, encrypted_password, Email, created_at, organizations, cards) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, user.username, user.display_name, encrypt_password(user.password), user.email, datetime.datetime.now(), "[]", "[]"))
        conn.commit()
        print(encrypt_password(user.password))
        return {"token": create_token(user_id), "user_id": user_id}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/users/{user_id}/")
def get_user(user_id: str):
    if user_id == "-1":
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, Email, created_at, super_admin FROM users")
        users = cursor.fetchall()
        print(users)
        return [{"id": user[0], "username": user[1], "display_name": user[2], "email": user[3], "created_at": user[4], "is_super_admin":user[5]} for user in users]
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, Email, created_at, super_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "display_name": user[2],
                "email": user[3],
                "created_at": user[4],
                "is_super_admin":user[5]
            }
        else:
            return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.post("/login/")
def login(login_request: LoginRequest):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, encrypted_password FROM users WHERE username = ?", (login_request.username,))
        user = cursor.fetchone()
        if user:
            print(encrypt_password(login_request.password))
            print(user[1])
            stored_password = user[1]
            if bcrypt.checkpw(login_request.password.encode('utf-8'), stored_password.encode('utf-8')):
                token = create_token(user[0])
                return {"logged_in": True,"token":token, "user_id": user[0]}
            else:
                return {"logged_in": False, "error": "Invalid username or password"}
        else:
            return {"logged_in": False, "error": "Invalid username or password"}
    except Exception as e:
        print(str(e))
        raise fastapi.HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/new_organization/")
def add_organization(form: Organization):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pending_accounts (name, owner_id, description) VALUES (?, ?, ?)",
                    (form.name, form.owner_id, form.description))
        conn.commit()
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/pending_accounts/")
def get_pending_accounts():
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, owner_id, description FROM pending_accounts")
        accounts = cursor.fetchall()
        return [{"id": account[0], "name": account[1], "owner_id": account[2], "description": account[3]} for account in accounts]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.post("/approve_account/{account_id}")
def approve_account(account_name: str, super_admin_token: str):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        token_data = decode_token(super_admin_token)
        if not token_data.get("is_super_admin"):
            raise fastapi.HTTPException(status_code=403, detail="Only super admins can approve accounts")
        cursor.execute("SELECT name, owner_id FROM pending_accounts WHERE name = ?", (account_name,))
        account = cursor.fetchone()
        if account:
            account_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO organizations (id, name, balance, owner_id, created_at, members, approver) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (account_id, account[0], 0.0, account[1], datetime.datetime.now(), "[]", token_data["user_id"]))
            cursor.execute("DELETE FROM pending_accounts WHERE name = ?", (account_name,))
            conn.commit()
            return {"message": "Account approved and created successfully"}
        else:
            return {"error": "Pending account not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/organizations/{account_id}")
def get_bank_account(account_id: str):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT organizations.id, organizations.name, organizations.balance, users.display_name, organizations.created_at FROM organizations JOIN users ON organizations.id = users.id WHERE organizations.id = ?", (account_id,))
        account = cursor.fetchone()
        if account:
            return {
                "id": account[0],
                "name": account[1],
                "balance": account[2],
                "owner_name": account[3],
                "created_at": account[4]
            }
        else:
            return {"error": "Bank account not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


@app.get("/users/{user_id}/organizations/")
def get_organizations(user_id: Optional[str] = None):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT organizations.id, organizations.name, organizations.balance, users.display_name, organizations.created_at FROM organizations JOIN users ON organizations.id = users.id and users.id = ?",(user_id,))
        else:
            cursor.execute("SELECT organizations.id, organizations.name, organizations.balance, users.display_name, organizations.created_at FROM organizations JOIN users ON organizations.id = users.id")
        accounts = cursor.fetchall()
        return [{"id": account[0], "name": account[1], "balance": account[2], "owner_name": account[3], "created_at": account[4]} for account in accounts]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
@app.post("/new_transaction/")
def new_transaction(transaction: Transaction):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        transaction_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO transactions (id, title, sender_bank_account_id, sender_user_id, receiver_bank_account_id, amount, timestamp, notes, receipts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (transaction_id, transaction.title, transaction.sender_bank_account_id, transaction.sender_user_id, transaction.receiver_bank_account_id, transaction.amount, datetime.datetime.now()))
        conn.commit()
        return {
            "transaction_id": transaction_id,
            "title": transaction.title,
            "sender_bank_account_id": transaction.sender_bank_account_id,
            "sender_user_id": transaction.sender_user_id,
            "receiver_bank_account_id": transaction.receiver_bank_account_id,
            "amount": transaction.amount,
            "timestamp": datetime.datetime.now()
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, sender_bank_account_id, sender_user_id, receiver_bank_account_id, amount, timestamp FROM transactions WHERE id = ?", (transaction_id,))
        transaction = cursor.fetchone()
        if transaction:
            return {
                "id": transaction[0],
                "title": transaction[1],
                "sender_bank_account_id": transaction[2],
                "sender_user_id": transaction[3],
                "receiver_bank_account_id": transaction[4],
                "amount": transaction[5],
                "timestamp": transaction[6]
            }
        else:
            return {"error": "Transaction not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.post("/new_card/")
def new_card(card: Card):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        card_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO cards (id, card_name, card_holder_id, card_number, expiration_date, cvv, bank_account_id, spending_limit, spent_money) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (card_id, card.card_name, card.card_holder_id, fake.credit_card_number(), fake.credit_card_expire(), fake.credit_card_security_code(), card.bank_account_id, card.spending_limit, 0.0))
        conn.commit()
        return {
            "card_id": card_id,
            "card_name": card.card_name,
            "card_holder_id": card.card_holder_id,
            "bank_account_id": card.bank_account_id,
            "card_number": fake.credit_card_number(),
            "expiration_date": fake.credit_card_expire(),
            "cvv": fake.credit_card_security_code(),
            "spending_limit": card.spending_limit
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/cards/{card_id}")
def get_card(card_id: str):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, card_name, card_holder_id, card_number, expiration_date, cvv, bank_account_id, spending_limit, spent_money FROM cards WHERE id = ?",
                       (card_id,))
        card = cursor.fetchone()
        if card:
            return {
                "id": card[0],
                "card_name": card[1],
                "card_holder_id": card[2],
                "card_number": card[3],
                "expiration_date": card[4],
                "cvv": card[5],
                "bank_account_id": card[6],
                "spending_limit": card[7],
                "spent_money": card[8]
            }
        else:
            return {"error": "Card not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.post("/spend/")
def spend(card: CardTransaction):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT spending_limit, spent_money, cvv, expiration_date FROM cards WHERE card_number = ?", (card.card_number,))
        card_data = cursor.fetchone()
        if card_data:
            if card_data[2] != card.cvv:
                return {"error": "Invalid CVV"}
            if card_data[3] < datetime.datetime.now().strftime("%Y-%m-%d"):
                return {"error": "Card has expired"}
            if card_data[1] + card.amount > card_data[0]:
                return {"error": "Spending limit exceeded"}
            cursor.execute("UPDATE cards SET spent_money = spent_money + ? WHERE id = ?", (card.amount, card.card_id))
            conn.commit()
            return {"message": "Transaction successful"}
        else:
            return {"error": "Card not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()



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
import stripe

fake = faker.Faker()
SECRET_KEY = os.getenv("secret_key")
ALGORITHM = os.getenv("algorithm")
stripe.api_key = os.getenv("SSK")

sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("timestamp", lambda v: datetime.datetime.fromisoformat(v.decode()))

database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

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
    conn = sqlite3.connect(database_path)
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
        print("Invalid token")
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
    description: str

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

class Token(pydantic.BaseModel):
    token: str

class StripeCheckout(pydantic.BaseModel):
    amount: int
    organization_id: str
    title: str
    token: str
    user_id: str
    sucess: str
    fail: str

@app.post("/register/")
def add_user(user: User):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            return {"error": "Username already exists"}
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
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, display_name, Email, created_at, super_admin FROM users")
        users = cursor.fetchall()
        print(users)
        return [{"id": user[0], "username": user[1], "display_name": user[2], "email": user[3], "created_at": user[4], "is_super_admin":user[5]} for user in users]
    try:
        conn = sqlite3.connect(database_path)
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
        conn = sqlite3.connect(database_path)
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
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM pending_accounts WHERE name = ?", (form.name,))
        if cursor.fetchone():
            raise fastapi.HTTPException(status_code=403, detail="Organization name already exists in pending accounts")
        cursor.execute("SELECT name FROM organizations WHERE name = ?", (form.name,))
        if cursor.fetchone():
            raise fastapi.HTTPException(status_code=403, detail="Organization name already exists")
        cursor.execute("INSERT INTO organizations (id, name, description, balance, owner_id, created_at, members, approver) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (uuid.uuid4(),form.name, form.description, 0.0, form.owner_id, datetime.datetime.now(), f"[{form.owner_id}]", "hi"))
        conn.commit()
        return {"message": "Organization request submitted successfully"}
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/organizations/{account_id}/")
def get_bank_account(account_id: str):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations where id = ?", (account_id,))
        account = cursor.fetchone()
        if account:
            return {
                "id": account[0],
                "name": account[1],
                "description": account[2],
                "balance": account[3],
                "owner_id": account[4],
                "created_at": account[5],
                "members": account[6]
            }
        else:
            return {"error": "Bank account not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/organization/{account_id}/members/")
def get_members(account_id: str):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT members FROM organizations where id = ?", (account_id,))
        members = cursor.fetchone()
        result = []
        for member in members[0][1:-1].split(","):
            cursor.execute("SELECT username FROM users where id = ?", (member,))
            result.append(cursor.fetchone())
        if members:
            return {"members": result}
        else:
            return {"error": "Organization not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/users/{user_id}/organizations/")
def get_organizations(user_id: Optional[str] = None):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations")
        organizations = cursor.fetchall()
        result = []
        for org in organizations:
            if org[6] and user_id in org[6]:
                result.append({"id": org[0], "name": org[1],"description": org[2], "balance": org[3], "owner_id": org[4], "created_at": org[5]})
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
@app.post("/new_transaction/")
def new_transaction(transaction: Transaction):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        transaction_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO transactions (id, title, sender_bank_account_id, sender_user_id, receiver_bank_account_id, amount, timestamp, notes, receipts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (transaction_id, transaction.title, transaction.sender_bank_account_id, transaction.sender_user_id, transaction.receiver_bank_account_id, transaction.amount, datetime.datetime.now(), "[]", "[]"))
        cursor.execute("UPDATE organizations SET balance = balance - ? WHERE id = ?", (transaction.amount, transaction.sender_bank_account_id))
        cursor.execute("UPDATE organizations SET balance = balance + ? WHERE id = ?", (transaction.amount, transaction.receiver_bank_account_id))
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

@app.get("/transactions/{transaction_id}/")
def get_transaction(transaction_id: str):
    try:
        conn = sqlite3.connect(database_path)
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

@app.get("/organization/{account_id}/transactions/")
def get_organization_transactions(account_id: str):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE sender_bank_account_id = ? OR receiver_bank_account_id = ?", (account_id, account_id))
        transactions = cursor.fetchall()
        for i in range(len(transactions)):
            print(transactions[i])
            transaction = list(transactions[i])
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (transaction[2],))
            reciever_name = cursor.fetchone()
            if reciever_name:
                transaction[2] = reciever_name[0]
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (transaction[4],))
            sender_name = cursor.fetchone()
            if sender_name:
                transaction[4] = sender_name[0]
            transactions[i] = tuple(transaction)
            print(transactions[i])
        return [{
            "id": transaction[0],
            "title": transaction[1],
            "sender_bank_account_id": transaction[2],
            "sender_user_id": transaction[3],
            "receiver_bank_account_id": transaction[4],
            "amount": transaction[5],
            "timestamp": transaction[6]
        } for transaction in transactions]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
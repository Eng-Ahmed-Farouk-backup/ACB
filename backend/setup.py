import sqlite3

def setup():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    balance REAL NOT NULL,
                    owner_id TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    members TEXT NOT NULL,
                    approver TEXT NOT NULL
                )""")
    
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    sender_bank_account_id TEXT NOT NULL,
                    sender_user_id TEXT NOT NULL,
                    receiver_bank_account_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    notes TEXT,
                    receipts TEXT
                )""")
    
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    encrypted_password TEXT NOT NULL,
                    Email TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    organizations TEXT NOT NULL,
                    cards TEXT NOT NULL,
                    super_admin BOOLEAN NOT NULL DEFAULT 0
                )""")
    
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id TEXT PRIMARY KEY,
                    card_name TEXT NOT NULL,
                    card_holder_id TEXT NOT NULL,
                    card_number TEXT NOT NULL,
                    expiration_date DATETIME NOT NULL,
                    cvv TEXT NOT NULL,
                    bank_account_id TEXT NOT NULL,
                    spending_limit REAL NOT NULL,
                    spent_money REAL NOT NULL
                )""")
    
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    noted_at DATETIME NOT NULL,
                    noter_id TEXT NOT NULL
                )""")
    
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_accounts (
                    name TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    description TEXT NOT NULL
                )""")
    
    conn.commit()
    conn.close()

def reset_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS organizations")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cards")
    cursor.execute("DROP TABLE IF EXISTS notes")
    cursor.execute("DROP TABLE IF EXISTS pending_accounts")
    setup()
    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset_database()
    print("Database setup completed.")
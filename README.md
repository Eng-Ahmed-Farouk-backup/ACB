# ACB - Organization Finances Management System

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Railway](https://img.shields.io/badge/deployed%20on-Railway-131415.svg)](https://railway.app/)


**This is a Platform system for Founders who wants to show their team members their organization Finance and turn it to a Financilly Transparent Organization**
---

## Features

### For Organization Owner
- **Add Transfers** – Add a deposit (donation / fund etc.) and a Withdraw (Fund for other org / buy things etc.)
  
- **Transactions** – See the Full history of Recent Transactions
  
### For Members
- **Organization Dashboard** – See balance, members, and transactions
  
- **Transactions** – See the Full history of Recent Transactions

---

## Project Structure

```

ACB/
├── backend/
│   ├── main.py              # FastAPI application with all endpoints
│   ├── setup.py             # Database Creation and super admin
│   ├── requirements.txt     # Python requirements
│   └── database.db          # SQLite database (created at runtime)
├── front end/
│   ├── login/               # Login page
│   │   ├── login.html
│   │   ├── login.css
│   │   └── login.js
│   ├── register/            # Registration page
│   │   ├── register.html
│   │   ├── register.css
│   │   └── register.js
│   ├── dashboard/           # User dashboard
│   │   ├── dashboard.html
│   │   ├── dashboard.css
│   │   └── dashboard.js
│   ├── organization/        # Organization Dashboard
│   │   ├── organization.html
│   │   ├── organization.css
│   │   └── organization.js
│   ├── create_organization/ # New organization form page
│   │   ├── create_organization.html
│   │   ├── create_organization.css
│   │   └── create_organization.js
└── README.md # that's what yo are reading right now!

```

---
## How to try 
go to : https://eng-ahmed-farouk-backup.github.io/ACB/front%20end/login/login.html

Make an Account and create an Organization then add transactions and share your organization link to your members to see the transactions history 


that's it have fun !

## How to try (DEVELOPER MODE)

### Backend Setup

1. **Clone the Repo**
```bash
git clone https://github.com/Eng-Ahmed-Farouk-backup/ACB.git
cd ACB
```

2. **go to backend folder**
```bash
cd backend
```

3. **Install the requirements**
```bash
pip install -r requirements.txt
```

5. **Create the database**
```bash
python setup.py
```
6. **Run the backend server**
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`


7. **Open the application**
run login.html in your browser and have fun !
---
# Logo 
I made this Logo using Canva but Didn't put it on the Website becuase this is the 1st logo Draft 
<img width="2000" height="2000" alt="ACB Branding (1)" src="https://github.com/user-attachments/assets/f6cae190-7a42-4ee3-b9f3-63c7a00a8b4d" />

# Author
this is Platform Made By Ahmed Farouk
Passionate about STEAM, Entrepreneurship 

- Leader of Innovations Hack Club
- Founder & CEO of Adapt Community
- Present Contractor @ Hack club under the Management of Christina (the co founder)

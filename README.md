# Personal-Finance-Manager
# 💰 Personal Finance Project

A **Django-based Personal Finance Management System** that helps you track **budgets, accounts, transactions, and expenses** with **beautiful interactive charts** for better financial insights.  
Includes **live balance tracking**, **category & budget management**, and a **dashboard** with daily/monthly graphs.

---

## 📌 Features

### 🏠 Dashboard
- **Live Money Card** — Shows current balance after subtracting transactions & expenses.
- **Monthly Budgets Graph** — Displays budget allocations per category.
- **Daily Transactions Chart** — Shows expense trends for the current month.
- **This Month's Expenses Summary** — Quick overview of spending.

### 💳 Accounts
- Create, edit, and delete accounts.
- Live balances shown for each account.
- **Transfers between accounts** with automatic paired in/out transactions.
- Filter transactions by account.

### 📂 Categories & Budgets
- Create, edit, and delete categories (with safety check if linked to transactions).
- Assign monthly budgets to categories.
- Budget utilization tracking.

### 💵 Transactions
- Add income and expenses.
- Assign categories & accounts.
- View transaction history.
- Filter transactions by account & date.

---

## 🖥️ Tech Stack

- **Backend:** Django (Python)
- **Database:** MySQL / MariaDB
- **Frontend:** Tailwind CSS + Chart.js
- **Environment:** Python venv
<!-- - **Hosting:** VPS-ready (e.g., Hostinger, DigitalOcean) -->

---

## 📂 Project Structure

personal_finance_project/
├── accounts/ # Account management app
├── budgets/ # Budgets & category tracking
├── transactions/ # Income & expense logging
├── dashboard/ # Dashboard & charts
├── templates/ # HTML templates (Tailwind)
├── static/ # CSS, JS, images
├── docs/images/ # Project screenshots
├── manage.py
└── requirements.txt

## ⚙️ Installation & Setup
### 1️. Clone the Repository

git clone https://github.com/Arif-Shafwan/Personal-Finance-Manager.git
cd personal-finance-project

### 2. Create Virtual Environment & Install Dependencies

python -m venv .venv
source .venv/bin/activate   # On Linux/Mac
.venv\Scripts\activate      # On Windows

pip install -r requirements.txt

### 3. Edit settings.py to match your MySQL credentials:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'looyall2',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

### 4. Run Migrations
python manage.py makemigrations
python manage.py migrate


### 5. Create Superuser (For SQLlite3) - Optional
python manage.py createsuperuser

### 6. Start Server
python manage.py runserver


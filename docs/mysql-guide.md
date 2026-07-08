# MySQL Guide for CarDealTZ CRM

Everything your team needs to know about MySQL for this project — from first-time
setup to day-to-day commands.

---

## Table of Contents

1. [Installation (Windows)](#1-installation-windows)
2. [Installation (Linux)](#2-installation-linux)
3. [Starting & Stopping MySQL](#3-starting--stopping-mysql)
4. [Connecting to MySQL](#4-connecting-to-mysql)
5. [Database & User Management](#5-database--user-management)
6. [Reset Lost Root Password](#6-reset-lost-root-password)
7. [Django Migrations](#7-django-migrations)
8. [Exploring the Database](#8-exploring-the-database)
9. [Import / Export](#9-import--export)
10. [Common Problems](#10-common-problems)
11. [Quick Reference](#11-quick-reference)

---

## 1. Installation (Windows)

### Option A — MySQL Installer (recommended)

1. Download from <https://dev.mysql.com/downloads/installer/>
2. Run the installer, choose **Developer Default**
3. During setup:
   - **Root password**: set a password you will remember. If you forget, see
     Section 6 below.
   - **MySQL as a Windows Service**: check this — it keeps MySQL running in the
     background after reboot.
4. After install, MySQL runs automatically. Open **MySQL 8.0 Command Line Client**
   from the Start Menu to get a prompt.

### Option B — XAMPP (easier but older MySQL)

1. Download from <https://www.apachefriends.org/>
2. Install, then open the **XAMPP Control Panel**
3. Click **Start** next to **MySQL**
4. Click **Shell** and type: `mysql -u root`

---

## 2. Installation (Linux)

```bash
sudo apt update
sudo apt install mysql-server -y
sudo systemctl start mysql
sudo systemctl enable mysql   # auto-start on boot
```

After installing, secure your installation:

```bash
sudo mysql_secure_installation
```

This will ask you to:
- Set a root password
- Remove anonymous users
- Disallow remote root login
- Remove test databases

---

## 3. Starting & Stopping MySQL

### Linux

```bash
# Check if MySQL is running
sudo systemctl status mysql

# Start
sudo systemctl start mysql

# Stop
sudo systemctl stop mysql

# Restart
sudo systemctl restart mysql

# Auto-start on boot
sudo systemctl enable mysql
```

### Windows (installed as a service)

```powershell
# Open PowerShell as Administrator
net start MySQL80
net stop MySQL80
```

### Windows (XAMPP)

Open XAMPP Control Panel → click Start/Stop next to MySQL.

---

## 4. Connecting to MySQL

### As root (Linux — auth_socket plugin)

```bash
sudo mysql -u root
```

If that fails, try:

```bash
mysql -u root -p
# then type your root password when prompted
```

### As root (Windows)

```powershell
mysql -u root -p
```

### As a specific user

```bash
mysql -u root -p car_crm
```

The last argument (`car_crm`) selects the database immediately.

### From Python / Django

Django connects automatically using the `DATABASES` setting in
`car_crm/settings.py`. When `USE_MYSQL=True`, it reads:

| Setting        | Env Variable     | Default     |
|----------------|------------------|-------------|
| Database name  | `DB_NAME`        | `car_crm`   |
| User           | `DB_USER`        | `root`      |
| Password       | `DB_PASSWORD`    | (empty)     |
| Host           | `DB_HOST`        | `localhost` |
| Port           | `DB_PORT`        | `3306`      |

These are loaded from `.env` (gitignored — keep it secret).

---

## 5. Database & User Management

### Create a new database

```sql
CREATE DATABASE car_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- `utf8mb4` supports emoji and special characters (unlike plain `utf8`)
- `utf8mb4_unicode_ci` is a case-insensitive collation

### Delete a database

```sql
DROP DATABASE car_crm;
```

### Show all databases

```sql
SHOW DATABASES;
```

### Select a database (use it)

```sql
USE car_crm;
```

### Create a new MySQL user

```sql
CREATE USER 'car_user'@'localhost' IDENTIFIED BY 'strongpassword123';
```

### Grant all privileges on a database to a user

```sql
GRANT ALL PRIVILEGES ON car_crm.* TO 'car_user'@'localhost';
FLUSH PRIVILEGES;
```

- `car_crm.*` means "all tables in the car_crm database"
- `FLUSH PRIVILEGES` reloads the grant tables so the change takes effect
  immediately

### Grant specific privileges (more secure)

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON car_crm.* TO 'car_user'@'localhost';
```

### Show all users

```sql
SELECT User, Host FROM mysql.user;
```

### Change a user's password

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';
```

### Delete a user

```sql
DROP USER 'car_user'@'localhost';
```

---

## 6. Reset Lost Root Password

If you forgot the MySQL root password, follow these steps:

### Step 1: Stop MySQL

```bash
sudo systemctl stop mysql     # Linux
net stop MySQL80              # Windows (PowerShell as Admin)
```

### Step 2: Start MySQL in safe mode (skip authentication)

```bash
sudo mysqld_safe --skip-grant-tables &
```

On some systems, use:

```bash
sudo mkdir -p /var/run/mysqld
sudo chown mysql:mysql /var/run/mysqld
sudo mysqld --skip-grant-tables --skip-networking &
```

### Step 3: Connect without a password

```bash
mysql -u root
```

### Step 4: Reset the password

```sql
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';
```

Note: `FLUSH PRIVILEGES` is needed here because we started with
`--skip-grant-tables`, which disables privilege checking. We must reload them
before `ALTER USER` will work.

### Step 5: Stop safe mode and restart normally

```bash
# Kill the safe-mode MySQL process
sudo pkill mysqld
sudo pkill mysqld_safe

# Start MySQL normally
sudo systemctl start mysql
```

Then verify:

```bash
mysql -u root -p
# enter your new password
```

---

## 7. Django Migrations

### How migrations work

1. Django compares your `models.py` to the current database schema
2. It generates a migration file (Python) with the changes
3. You apply the migration file to actually modify the database

### See pending migrations

```bash
source venv/bin/activate
source .env
python3 manage.py showmigrations
```

Migrations with `[X]` are applied. Migrations with `[ ]` are pending.

### Create a new migration (after changing models.py)

```bash
python3 manage.py makemigrations
```

This creates files like `advertising/migrations/0001_initial.py`.

To see what SQL will be executed:

```bash
python3 manage.py sqlmigrate advertising 0001
```

### Apply migrations to MySQL

```bash
python3 manage.py migrate
```

This runs all pending migrations against the MySQL database.

### Roll back a migration

```bash
python3 manage.py migrate advertising 0001
```

Replace `0001` with the migration you want to go back to.

### Check which tables Django created

```sql
USE car_crm;
SHOW TABLES;
```

You should see tables like:
- `accounts_customuser`
- `vehicles_vehicle`
- `vehicles_vehicleimage`
- `leads_lead`
- `leads_appointment`
- `advertising_banner`
- `advertising_promotion`
- `campaigns_campaign`
- `campaigns_campaignlead`
- `chatbot_chatsession`
- `chatbot_chatmessage`
- `notifications_smslog`
- `django_migrations`   (tracks which migrations have been applied)
- `django_session`      (stores user sessions)
- `django_admin_log`    (logs admin actions)

### Reset a specific app's tables

```bash
python3 manage.py migrate advertising zero
```

This undoes ALL migrations for the `advertising` app.

---

## 8. Exploring the Database

### List all tables in the current database

```sql
SHOW TABLES;
```

### Show the structure of a table (columns, types, keys)

```sql
DESCRIBE accounts_customuser;
```

Or:

```sql
SHOW COLUMNS FROM accounts_customuser;
```

### View table creation SQL

```sql
SHOW CREATE TABLE accounts_customuser;
```

### Select all rows

```sql
SELECT * FROM accounts_customuser;
```

**Warning**: `SELECT *` without `LIMIT` can dump thousands of rows. Always add:

```sql
SELECT * FROM accounts_customuser LIMIT 10;
```

### Select specific columns

```sql
SELECT id, username, phone, role FROM accounts_customuser;
```

### Filter rows

```sql
SELECT * FROM accounts_customuser WHERE role = 'staff';
SELECT * FROM accounts_customuser WHERE phone LIKE '+255%';
```

### Count rows

```sql
SELECT COUNT(*) FROM vehicles_vehicle;
SELECT role, COUNT(*) FROM accounts_customuser GROUP BY role;
```

### Sort results

```sql
SELECT * FROM vehicles_vehicle ORDER BY price DESC LIMIT 5;
```

### Joins — linking related tables

Show each lead with its assigned staff member's name:

```sql
SELECT
    l.id,
    l.customer_name,
    l.customer_phone,
    u.username AS assigned_to
FROM leads_lead l
LEFT JOIN accounts_customuser u ON l.assigned_to_id = u.id
LIMIT 10;
```

### See Django's migration history

```sql
SELECT app, name, applied FROM django_migrations ORDER BY applied DESC;
```

---

## 9. Import / Export

### Export the entire database

```bash
mysqldump -u root -p car_crm > car_crm_backup.sql
```

This creates a text file with all the SQL commands needed to recreate the
database and data.

### Export a single table

```bash
mysqldump -u root -p car_crm accounts_customuser > users_backup.sql
```

### Export without data (schema only)

```bash
mysqldump --no-data -u root -p car_crm > car_crm_schema.sql
```

### Import a backup

```bash
mysql -u root -p car_crm < car_crm_backup.sql
```

Or from within MySQL:

```sql
USE car_crm;
SOURCE /path/to/car_crm_backup.sql;
```

### Export with Docker

If MySQL is running in Docker:

```bash
docker exec -i mysql_container mysqldump -u root -p car_crm > backup.sql
```

---

## 10. Common Problems

### Problem: "Access denied for user 'root'@'localhost' (using password: NO)"

**Cause**: Django is trying to connect without a password but MySQL requires one.

**Fix**: Make sure `.env` has `DB_PASSWORD=darkknight` (or your actual password)
and that you are sourcing it properly:

```bash
set -a; source .env; set +a
python3 manage.py runserver
```

Or use `bash start.sh` (which does this automatically).

### Problem: "Access denied for user 'root'@'localhost' (using password: YES)"

**Cause**: The password in `.env` is wrong.

**Fix**: Reset the root password (Section 6) or update `.env` with the correct
password.

### Problem: MySQL won't start

**Check 1** — Is another process using the port?

```bash
sudo lsof -i :3306
```

**Check 2** — Is the error log telling us why?

```bash
sudo tail -50 /var/log/mysql/error.log
```

**Check 3** — Is the disk full?

```bash
df -h
```

### Problem: "Unknown database 'car_crm'"

**Cause**: The database hasn't been created yet.

**Fix**:

```bash
mysql -u root -p -e "CREATE DATABASE car_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Then run migrations:

```bash
python3 manage.py migrate
```

### Problem: "Table '...' already exists"

**Cause**: A migration failed midway or you're running migrate on an existing
database.

**Fix**: Fake the migration as already applied:

```bash
python3 manage.py migrate --fake
```

### Problem: Port 3306 already in use

**Fix**: Find and kill the process using port 3306:

```bash
sudo fuser -k 3306/tcp
sudo systemctl start mysql
```

---

## 11. Quick Reference

### Most-used MySQL commands

| Command | What it does |
|---------|-------------|
| `mysql -u root -p` | Connect to MySQL |
| `SHOW DATABASES;` | List all databases |
| `USE car_crm;` | Select the car_crm database |
| `SHOW TABLES;` | List all tables in the current database |
| `DESCRIBE table_name;` | Show columns of a table |
| `SELECT * FROM table LIMIT 10;` | View 10 rows from a table |
| `DROP DATABASE car_crm;` | Delete the entire database (careful!) |
| `mysqldump -u root -p car_crm > backup.sql` | Backup the database |

### Django + MySQL workflow

```bash
# 1. Start MySQL (if not already running)
sudo systemctl start mysql

# 2. Activate environment + load DB password
set -a; source .env; set +a

# 3. Create database (first time only)
mysql -u root -p -e "CREATE DATABASE car_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. Apply all migrations
python3 manage.py migrate

# 5. Seed data (optional)
python3 manage.py seed_data

# 6. Run the server
python3 manage.py runserver
```

### Our .env file (gitignored — keep it safe)

```
SENDAFRICA_API_KEY=687c72abc476d89ae3584f72c207b223beb84086e51071d8ea21f60833a10172
DB_PASSWORD=darkknight
```

### MySQL config file location

| OS      | Location                    |
|---------|-----------------------------|
| Linux   | `/etc/mysql/my.cnf`         |
| Windows | `C:\ProgramData\MySQL\MySQL Server 8.0\my.ini` |
| XAMPP   | `C:\xampp\mysql\bin\my.ini` |

---

> **Tip for the team**: The easiest way to explore the database without the
> command line is MySQL Workbench (free) or TablePlus (paid but has a free tier).
> Both let you browse tables, run queries, and see relationships visually.

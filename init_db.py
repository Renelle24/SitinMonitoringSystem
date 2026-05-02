import MySQLdb

conn = MySQLdb.connect(
    host="localhost",
    user="root",
    password="",
    port=3306
)

cur = conn.cursor()

# Create database
cur.execute("CREATE DATABASE IF NOT EXISTS sitin_db")
cur.execute("USE sitin_db")

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    id VARCHAR(20) PRIMARY KEY,
    last VARCHAR(50),
    first VARCHAR(50),
    middle VARCHAR(50),
    year INT,
    course VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(200),
    session INT DEFAULT 30,
    password VARCHAR(100)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sitin_records (
    sit_id VARCHAR(20) PRIMARY KEY,
    student_id VARCHAR(20),
    name VARCHAR(100),
    purpose VARCHAR(100),
    lab VARCHAR(50),
    session INT,
    status VARCHAR(20),
    date VARCHAR(30)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20),
    name VARCHAR(100),
    lab VARCHAR(50),
    purpose VARCHAR(100),
    date VARCHAR(20),
    time VARCHAR(10),
    status VARCHAR(20) DEFAULT 'Pending'
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author VARCHAR(50),
    date VARCHAR(30),
    body TEXT
)
""")

conn.commit()
cur.close()
conn.close()

print("Database and tables created successfully!")

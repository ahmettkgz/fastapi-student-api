import os
import psycopg2
from fastapi import Depends

# Veritabanı bağlantısı için ortam değişkenleri tanımla
DB_NAME = os.getenv("DB_NAME", "dbname")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pass")
DB_HOST = os.getenv("DB_HOST", "hostname")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# Dependency: her route'ta db bağlantısı almak için
def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
import sqlite3
from sqlite3 import Error

BACKUP = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\backup.db"

def db_connect(db_path):
    """ A simple fuction to make connection to SQLite databases easier """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
    except Error as e:
        print(e)
        conn.close()
    else:  
        return db, conn

def db_backup(existing_db):
    try:
        conn = sqlite3.connect(existing_db)
        bck = sqlite3.connect(BACKUP)
    except Error as e:
        print(e)
        conn.close()

    with bck:
        conn.backup(bck)

    conn.close()
    bck.close()

def db_restore(existing_db):
    try:
        conn = sqlite3.connect(existing_db)
        bck = sqlite3.connect(BACKUP)
    except Error as e:
        print(e)
        conn.close()
        
    with conn:
        bck.backup(conn)

    conn.close()
    bck.close()
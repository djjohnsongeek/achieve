import sqlite3
from sqlite3 import Error

def db_connect(URL):
    """ A simple fuction to make connection to SQLite databases easier """
    try:
        conn = sqlite3.connect(URL)
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
    except Error as e:
        print(e)
        conn.close()
    else:  
        return db, conn
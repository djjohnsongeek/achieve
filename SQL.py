import sqlite3
from sqlite3 import Error
# simple fuction to make connection to SQLite databases easier
def db_connect(URL):
    # Attempt to create a connection to the database
    try:
        conn = sqlite3.connect(URL)
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        # in the case of an error, print said error and close the connection
    except Error as e:
        print(e)
        conn.close()
        print("Connection Failed")
    else:  
        return db, conn


# query the database
# try:
#        db.execute("SELECT * FROM clients") # NOTE: example query
#    except Error as e:
#        print("Error -", e)
#        conn.close()
#    else:
#        query = db.fetchone()
#        print(query["name"])
#        for items in query:
#            print(items)
#            conn.close()

import os
import sys
import sqlite3

from sqlite3 import Error
from sys import argv

KEY_TEXT = "rkjfawtphxuoievokbanzmycaksjdgoql"

#----------------------------------------- helper functions --------------------------------------------------------#
def toupper(char: str):
    """ converts letter to upper case if neccesary """
    if len(char) != 1:
        return None

    num = ord(char)
    if num >= 65 and num <= 90:
        return char
    
    elif num >= 97 and num <= 122:
        return chr(num - 32)

    else:
        return None

def tolower(char: str):
    """ converts letters to lowercase if necessary """
    if len(char) != 1:
        return None
    
    num = ord(char)
    if num >= 65 and num <= 90:
        return chr(num + 32)
    
    elif num >= 97 and num <= 122:
        return char

    else:
        return None

def unscramble(cypher_text: str):
    """ unscrables text, uses a string as the cypher key """
    i = 0
    plain_text = ""
    for char in cypher_text:

        if i > len(KEY_TEXT) - 1:
            i = 0
    
        if char.isalpha() and char.isupper():
            key = ord(toupper(KEY_TEXT[i])) - 65
            curr_index = ord(char) - 65
            new_index = (curr_index - key) % 26
            new_letter = 65 + new_index
            plain_text += chr(new_letter)

        elif char.isalpha() and char.islower():
            key = ord(tolower(KEY_TEXT[i])) - 97
            curr_index = ord(char) - 97
            new_index = (curr_index - key) % 26
            new_letter = 97 + new_index
            plain_text += chr(new_letter)

        else:
            plain_text += char

        i += 1
    
    return(plain_text)

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

def shorten_day(day: str):
    """ Takes a string and returns the first three letters as a string """

    container = [day[i] for i in range(3)]
    return "".join(container)
#----------------------------------------- end helper functions --------------------------------------------------------#

# ensure command is properly typed
if len(argv) != 2:
    print("Usage: python test.py 'filename'")
    sys.exit(1)

# prepare varibles
DB_PATH = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"
FILE_PATH = sys.path[0] + "\\" + argv[1]
f = open(FILE_PATH, "r")
current_day = f.readline().lower()
current_day.rstrip("\n")
curr_att_day = shorten_day(current_day)

# connect to database
db, conn = db_connect(DB_PATH)

# adjust variables and info depending of staff or client schedule
if argv[1][0] == "s":
    db.execute(f"SELECT name FROM staff WHERE {curr_att_day}=1")
    all_staff = [name for row in db.fetchall() for name in row]
    empty = ""
    sch_type = "STAFF"
else:
    schedule_type = "clients"
    db.execute(f"SELECT name FROM clients WHERE {curr_att_day}=1")
    all_staff = [unscramble(name) for row in db.fetchall() for name in row]
    empty = "0"
    sch_type = "CLIENT"
conn.close()

# sort names, prepare dictionary
all_staff.sort()
staff_details = {}
for staff in all_staff:
    staff_details[staff] = {"total session-hours": 0, "total open-hours": 0, "open-hours": [], "session-hours": []}

# read schedule file
try:
    with open(FILE_PATH, "r") as f:
        for line in f:
            # prepare input for parsing
            line = line.split(",")
            if len(line) < 2 or line[0] == "Name":
                continue
            classroom = line[2].strip("\n")
            line.pop()
            line.append(classroom)

            # parse input into dictionary
            if line[0] != "":
                name = line[0]

            if line[2] == empty:
                if line[1] not in staff_details[name]["open-hours"]:
                    staff_details[name]["open-hours"].append(line[1])
                    staff_details[name]["total open-hours"] += 1
            elif line[2] == "OUT":
                pass
            else:
                if line[1] not in staff_details[name]["session-hours"]:
                    staff_details[name]["session-hours"].append(line[1])
                    staff_details[name]["total session-hours"] += 1
except FileNotFoundError:
    print("File not found")
    sys.exit(1)

# write info to file, as well as terminal
with open(sch_type + "_schedule_details.txt", "w") as txtf:
    print(f"****{sch_type} SUMMARY****")
    txtf.write(f"****{sch_type}SUMMARY****\n")
    for item in staff_details.items():
        # print/write staff name and hear
        txtf.write("---------------------\n")
        print("---------------------")
        txtf.write(item[0].upper() + "\n")
        print(item[0].upper())
        txtf.write("---------------------\n")
        print("---------------------")

        # print/write summary data
        for stuff in item[1].items():
            txtf.write(stuff[0] + ": " + str(stuff[1]) + "\n")
            print(stuff[0] + ": " + str(stuff[1]))
        
        print("\n")
        txtf.write("\n")
    
    print(f"{sch_type} AVAILABILITY BY HOUR")
    txtf.write(f"{sch_type} AVAILABILITY BY HOUR\n")
    for time in [830, 930, 1030, 1130, 1230, 130, 230, 330, 430, 530]:
        txtf.write("---------------------\n")
        print("---------------------")
        txtf.write("\t" + str(time) + "\n")
        print("\t" + str(time))
        txtf.write("---------------------\n")
        print("---------------------")
        for staff in all_staff:
            if str(time) in staff_details[staff]["open-hours"]:
                txtf.write(staff + "\n")
                print(staff)

print("\n")
print("Analysis Finished")
print(f"File '{sch_type}_schedule_details.txt' created at {sys.path[0]}")
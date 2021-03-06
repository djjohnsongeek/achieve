import sys

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
#----------------------------------------- end helper functions --------------------------------------------------------#

# ensure command is properly typed
if len(argv) != 2:
    print("Usage: python test.py 'filename'")
    sys.exit(1)

# prepare varibles
DB_PATH = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"
FILE_PATH = sys.path[0] + "\\" + argv[1]

### get staff/client names list from file
try:
    with open(FILE_PATH, "r") as f:
        current_day = f.readline().lower()
        all_staff = []
        for line in f:
            line = line.split(",")
            if len(line) < 3 or line[0] == "Name" or line[0] == "":
                continue

            all_staff.append(line[0])
except FileNotFoundError:
    print("File not found")
    sys.exit(1)

# adjust variables and info depending of staff or client schedule
if argv[1][0] == "s":
    empty = ""
    sch_type = "Staff"
else:
    empty = "0"
    sch_type = "Client"

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
            if len(line) < 3 or line[0] == "Name":
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

# write info to terminal and file
with open(sch_type.lower() + "_schedule_details.txt", "w") as txtf:
    print(f" ****{sch_type} summary ****")
    txtf.write(f"**** {sch_type} summary ****\n")
    for item in staff_details.items():
        # print/write staff name and heading
        txtf.write("---------------------\n")
        print("---------------------")
        txtf.write(item[0].upper() + "\n")
        print(item[0].upper())
        txtf.write("---------------------\n")
        print("---------------------")

        for stuff in item[1].items():
            txtf.write(stuff[0] + ": " + str(stuff[1]) + "\n")
            print(stuff[0] + ": " + str(stuff[1]))
        
        print("\n")
        txtf.write("\n")
    
    # print/write staff summary by hour
    print(f"**** {sch_type} availability by hour ****")
    txtf.write(f"**** {sch_type} availability by hour ****\n")
    for time in [830, 930, 1030, 1130, 1230, 130, 230, 330, 430, 530]:
        # print/write staff name and heading
        txtf.write("---------------------\n")
        print("---------------------")
        txtf.write("\t" + str(time) + "\n")
        print("\t" + str(time))
        txtf.write("---------------------\n")
        print("---------------------")
        # print/write summary data by hour
        for staff in all_staff:
            if str(time) in staff_details[staff]["open-hours"]:
                txtf.write(staff + "\n")
                print(staff)
print("\n")
print("Analysis Finished")
print(f"File '{sch_type.lower()}_schedule_details.txt' created at {sys.path[0]}")
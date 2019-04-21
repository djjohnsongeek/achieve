import sqlite3
from SQL import db_connect
from random import randrange

DB_URL = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"

def insert_t1(client_name: str, client_ID: int, client_team: list, client_sch: dict, t1_processDone):
    """ Adds Tier 1 staff to the given client's schedule """

    # connect to database
    db, conn = db_connect(DB_URL)

    if t1_processDone == False:
        tier = 1
    elif t1_processDone == True:
        tier = 2

    # create list of client team members that are tier 1 or tier 2 TODO: re-write this section using one SQLite query and list comprehension
    client_team_t1 = []
    for staff in client_team:
        db.execute("SELECT tier FROM staff WHERE name=?", (staff,))
        staff_tier = db.fetchone()
        if staff_tier["tier"] == tier:
            client_team_t1.append(staff)

    # remove t1 staff who have already been scheduled (This rule prevents a staff member from being scheduled with one client for more then 2 hours a day)
    client_team_t1 = [staff for staff in client_team_t1 if staff not in client_sch.values()]

    # return None if no t1 teachers left
    if not client_team_t1:
        print("first return statement: None, True")
        return None, True

    # insert staff in client's schedule
    else:
        # randomly select staff from list
        i = randrange(0, len(client_team_t1))
        
        # find empty client hours
        items = client_sch.items()
        client_open_times = [item[0] for item in items if item[1] == 0]

        # check on staff's available hours IN-PROGRESS      
        # get schedule for selected staff memeber
        db.execute('SELECT "830", "930", "1030", "1130", "1230", "130", "230" FROM staff WHERE name=?', (client_team_t1[i],))
        staff_hours = db.fetchone()

        staff_sch = dict(staff_hours)
        
        # delete items in dictionary where staff is already scheduled
        dummy_list = [item for item in staff_sch.items()]
        for item in dummy_list:
            if item[1] != "none":
                del staff_sch[item[0]]

        staff_open_times = [int(times) for times in staff_sch.keys()]

        # remove times from the client's open time list if they are not in the staff's open times
        for time in client_open_times:
            if time not in staff_open_times:
                client_open_times.remove(time)
                
        #   update it as client schedules are updating it
        #   check against it while scheduling
        #   write final content in csv file

        # schedule for 2 hours
        if len(client_open_times) >= 2:
            j = 2
        elif len(client_open_times) == 1:
            j = 1
        else:
            print("no one to schedule from t1 team, move on to tier2?")
            print(type(client_sch))
            print(client_sch)
            return client_sch, True # currently this raises an error

        # update staff database NOTE: using formatted strings: is this dangerous since variables are not user generated?
        for k in range(j):
            client_sch[client_open_times[k]] = client_team_t1[i]
            db.execute(f'UPDATE staff SET "{client_open_times[k]}"=? WHERE name=?', (client_name, client_team_t1[i]))
            
        conn.commit()
        conn.close()
        return client_sch, False
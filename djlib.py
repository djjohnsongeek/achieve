import sqlite3
from SQL import db_connect
from random import randrange

DB_URL = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"

def insert_t1(client_name: str, client_ID: int, client_team: list, client_sch: dict):
    """ Adds Tier 1 staff to the given client's schedule """

    # connect to database
    db, conn = db_connect(DB_URL)

    # create list of client team members that are tier 1
    client_team_t1 = []
    for staff in client_team:
        db.execute("SELECT tier FROM staff WHERE name=?", (staff,))
        staff_tier = db.fetchone()
        if staff_tier["tier"] == 1:
            client_team_t1.append(staff)

    # remove t1 staff who have already been scheduled (This rule prevents a staff member from being scheduled with one client for more then 2 hours a day)
    dummy_list = client_team_t1.copy()
    for staff in dummy_list:
        if staff in client_sch.values():
            client_team_t1.remove(staff)

    # return None if no t1 teachers left
    if not client_team_t1:
        return None

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
        dummy_list2 = [item for item in staff_sch.items()]
        for item in dummy_list2:
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
            client_sch[client_open_times[0]] = client_team_t1[i]
            client_sch[client_open_times[1]] = client_team_t1[i]

            # update staff database NOTE: using formatted strings: is this dangerous since variables are not user generated?
            db.execute(f'UPDATE staff SET "{client_open_times[0]}"=? WHERE name=?', (client_name, client_team_t1[i]))
            db.execute(f'UPDATE staff SET "{client_open_times[1]}"=? WHERE name=?', (client_name, client_team_t1[i]))

        elif len(client_open_times) == 1:
            client_sch[client_open_times[0]] = client_team_t1[i]
            db.execute(f'UPDATE staff SET "{client_open_times[0]}"=? WHERE name=?', (client_name, client_team_t1[i]))
        else:
            print("no one to schedule from t1 team, move on to tier2?")
            
        conn.commit()
        conn.close()
        return(client_sch)
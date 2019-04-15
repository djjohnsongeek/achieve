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
        open_times = [item[0] for item in items if item[1] == 0]

        # check on staff's available hours TODO
        
        
        # get schedule for selected staff memeber
        db.execute('SELECT "830", "930", "1030", "1130", "1230", "130", "230" FROM staff WHERE name=?', (client_team_t1[i],))
        staff_hours = db.fetchone()
        staff_hours_keys = [int(times) for times in staff_hours.keys()]
        
        for time in staff_hours_keys:
            if time in open_times:
                print("he is free") # on the right track with this

        #   update it as client schedules are updating it
        #   check against it while scheduling
        #   write final content in csv file

        # schedule for 2 hours
        if len(open_times) >= 2:
            client_sch[open_times[0]] = client_team_t1[i]
            client_sch[open_times[1]] = client_team_t1[i]

        if len(open_times) < 2:
            client_sch[open_times[0]] = client_team_t1[i]

        conn.close()
        return(client_sch)
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

    # close connection to database
    conn.close()

    # check 0 tier 1 staff
    if not client_team_t1:
        return None

    # insert staff in client's schedule
    else:
        # randomly select staff from list
        i = randrange(0, len(client_team_t1))

        # find empty hours TODO
        items = client_sch.items()
        open_times = []
        for item in items:
            if item[1] == 0:
                open_times.append(item[0])
        
        
        # schedule for 2 hours
        if len(open_times) >= 2:
            client_sch[open_times[0]] = client_team_t1[i]
            client_sch[open_times[1]] = client_team_t1[i]

        # update staff dict TODO
        return(client_sch)
        


        # which are tier 2?
                # if any 
                    # schedule for 2 hours
                # if not 
                    # move to next tier
                # check for blank places on client's day
                    # if yes
                        # repeat process
                    # if no
                        # move on to next client

            # which are tier 3?
                # if any 
                    # schedule for 2 hours
                # if not 
                    # move to next tier
                # check for blank places on client's day
                    # if yes
                        # repeat process
                    # if no
                        # move on to next client
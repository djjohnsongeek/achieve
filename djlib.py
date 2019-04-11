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
    print("t1 team:", client_team_t1)
    # close connection to database
    conn.close()
    # remove t1 staff who have already been scheduled on the client's team
    for staff in client_team_t1:
        if staff in client_sch.values():
            client_team_t1.remove(staff)
    print("cleaned", client_team_t1)
    # return 0 if no t1 teachers left
    if not client_team_t1:
        return None

    # insert staff in client's schedule
    else:
        # randomly select staff from list
        i = randrange(0, len(client_team_t1))

        # find staff's available hours TODO

        # find empty client hours
        items = client_sch.items()
        open_times = [item[0] for item in items if item[1] == 0]
        
        # schedule for 2 hours
        if len(open_times) >= 2:
            client_sch[open_times[0]] = client_team_t1[i]
            client_sch[open_times[1]] = client_team_t1[i]

        if len(open_times) < 2:
            client_sch[open_times[0]] = client_team_t1[i]

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
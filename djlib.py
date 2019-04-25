import sqlite3

from random import randrange

from SQL import db_connect

DB_URL = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"

def generate_schedules(client_name: str, client_ID: int, client_team: list, client_sch: dict):
    """ 
    Adds staff to the given client's schedule, Schedules based on the following logic:
    -First uses available Team Members (first Tier 1, then 2, then 3) [DONE]
    -Second uses any available teacher except Program Supervisors (first Tier 1, then 2, then 3) [DONE: but disregards tier]
    -Third uses Program Supervisors [TODO]
    -Lastly outside of ABC subs [TODO]
    """
    # NOTE: need to review code, look for oppertunities for list comprehension
    # NOTE: function needs to check client and teacher's times (does it though? since the algorythm already removes times that don't match)

    # connect to database
    db, conn = db_connect(DB_URL)
    processDone = 0


    while 0 in client_sch.values():

        # create list of client team members that are tier 1 or tier 2
        if processDone == 0:    # Tier 1 Teachers on the client's team
            tier = 1
        elif processDone == 1:  # Tier 2 Teachers on the client's team
            tier = 2
        elif processDone == 2:  # Tier 3 Teachers on the client's team
            tier = 3
        elif processDone == 3:  # Sub teachers, any tier, any team
            db.execute('SELECT name FROM staff WHERE NOT tier=4')
            members = db.fetchall()
            client_team = [member["name"] for member in members]
            print(client_team)
                                
        tier_client_team = []
        for staff in client_team:
            if processDone == 3:
                tier_client_team.append(staff)
                continue
            db.execute("SELECT tier FROM staff WHERE name=?", (staff,))
            staff_tier = db.fetchone()
            if staff_tier["tier"] == tier:
                tier_client_team.append(staff)

        # remove t1 staff who have already been scheduled (This rule prevents a staff member from being scheduled with one client for more then 2 hours a day)
        tier_client_team = [staff for staff in tier_client_team if staff not in client_sch.values()]

        # check for no tier 2 teachers
        if not tier_client_team and processDone == 3:
            print("There are no available t1, t2, t3  or sub staff left on this client's team")
            break
        
        # if no tier 1 teachers restart with tier 2
        if not tier_client_team:
            print("There are no teachers left on this client's team, move to next group add 1")
            processDone += 1
            continue

        # insert staff in client's schedule (randomly select from list)
        i = randrange(0, len(tier_client_team))

        # find empty client hours
        items = client_sch.items()
        client_open_times = [item[0] for item in items if item[1] == 0]

        # check on staff's available hours IN-PROGRESS      
        # get schedule for selected staff memeber
        db.execute('SELECT "830", "930", "1030", "1130", "1230", "130", "230" FROM staff WHERE name=?', (tier_client_team[i],))
        staff_sch = dict(db.fetchone())

        # delete items in dictionary where staff is already scheduled
        dummy_list = [item for item in staff_sch.items()]
        for item in dummy_list:
            if item[1] != "none":
                staff_sch.pop(item[0], None)

        staff_open_times = [int(times) for times in staff_sch.keys()]

        # remove times from the client's open time list if they are not in the staff's open times (use list comprehension)
        client_open_times = [time for time in client_open_times if time in staff_open_times]

        # schedule for 2 hours
        if len(client_open_times) >= 2:
            j = 2
        elif len(client_open_times) == 1:
            j = 1
        else:
            if processDone == 3:
                print("loop ended, no available tier 1, 2, 3 or sub staff left")
                break
            else:
                print("There are no available staff at this tier, move up 1")
                processDone += 1
                continue

        # update staff database NOTE: using formatted strings: is this dangerous since variables are not user generated?
        for k in range(j):
            client_sch[client_open_times[k]] = tier_client_team[i]
            db.execute(f'UPDATE staff SET "{client_open_times[k]}"=? WHERE name=?', (client_name, tier_client_team[i]))
            conn.commit()

    conn.close()
    return client_sch
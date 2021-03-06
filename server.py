import sqlite3
import sys

from flask import session, request, redirect, render_template, flash
from functools import wraps
from random import randrange

from SQL import db_connect

DB_PATH = sys.path[0] + "\\achieve.db"
    
def login_required(f):
    """ decorates routes to require login """
    @wraps(f)
    def login_req(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return login_req

def admin_required(f):
    """ decorates route to require admin privlages """
    @wraps(f)
    def admin_req(*args, **kwargs):
        if session.get("user_id") != 0:
            session["error"] = 1
            flash("Your account is not permitted to access this page")
            return redirect("/")
        return f(*args, **kwargs)
    return admin_req

def convert_strtime(time_string: str):
    """ Takes a string with 12hr time information (such as '8:30') and strips away punctuation and returns a int """
    return int("".join(letter for letter in time_string if letter.isdigit()))
    
def create_schhours(times: str):
    """ Takes a start and endtime (integers) and creates a list of times seperated by an hour and ending at end """
    # TODO: deal with times that start on the hour (8:00) as well as times that start halfway through (8:30)
    time = times.split("-")
    start = convert_strtime(time[0])
    end = convert_strtime(time[1])

    hours = []
    while True:
        if start > end - 100:
            if len(hours) == 0:
                hours.append(start)
            break
        if start <= 1230:
            hours.append(start)
        else:
           hours.append(start - 1200)
        start += 100
    
    return hours

def shorten_day(day: str):
    """ Takes a string and returns the first three letters as a string """

    container = [day[i] for i in range(3)]
    return "".join(container)

def lengthen_day(day: str):
    """ Takes a short 'day' string and returns the string as a full day """
    if day in {"mon", "fri"}:
        return day + "day"
    elif day == "tue":
        return day + "sday"
    elif day == "wed":
        return day + "nesday"
    elif day == "thu":
        return day + "rsday"
    else:
        return None

def generate_schedules(client_ID: int, client_name: str, client_team: list, client_sch: dict, all_staff_sch: dict, att_day: str):
    """ 
    Adds staff to the given client's schedule, Schedules based on the following logic:
    -First uses available Team Members (first Tier 1, then 2, then 3) [DONE]
    -Second uses any available teacher except Program Supervisors (matches staff based on color class) [DONE]
    -Third uses Program Supervisors [TODO]
    -Lastly outside of ABC subs [TODO]
    """
    # NOTE: need to review code, performance improvements: additional loop that does does not regenerate entire t1_client_team list
    # NOTE: times for both clients and staff is static not dynamic
    # NOTE: need to devise a way to override "two hour only" scheduling, schedule based on team size

    # connect to database, prepare additional client specific variables
    db, conn = db_connect(DB_PATH)

    db.execute("SELECT totalhours FROM clients WHERE clientID=?", (client_ID,))
    client_data = db.fetchone()
    
    # decide the number of hours a client should be scheduled at a time, check for empty team
    team_size = len(client_team)
    if team_size < 1:
        schedule_var = 2
    else:
        schedule_var = round(client_data["totalhours"] / len(client_team) + .0001)
    if schedule_var == 1:
        schedule_var += 1

    current_step = 0
    # generates client schedule
    while 0 in client_sch.values():
        tier = current_step + 1

        if current_step == 3:  # Sub teachers: any tier, any team, only if color-class matches
            db.execute('SELECT color FROM clients WHERE clientID=?', (client_ID,))
            client_color = db.fetchone()
            db.execute(f'SELECT name, color FROM staff WHERE NOT tier=4 AND {att_day}=1')
            members = db.fetchall()
            client_team = [member["name"] for member in members if member["color"] >= client_color["color"]]

        # generate a dynamic list of scheduable staff                     
        tier_client_team = []
        for staff in client_team:
            if current_step == 3:
                tier_client_team.append(staff)
                continue

            db.execute(f"SELECT tier FROM staff WHERE name=? AND {att_day}=1", (staff,))
            staff_tier = db.fetchone()
            if staff_tier["tier"] == tier:
                tier_client_team.append(staff)

        # remove staff who have already been scheduled (This rule prevents a staff member from being scheduled with one client in more then one 'block')
        tier_client_team = [staff for staff in tier_client_team if staff not in client_sch.values()]

        # check for no sub teachers
        if not tier_client_team and current_step == 3:
            print("There are no available t1, t2, t3  or sub staff left on this client's team")
            break

        # if no teachers restart with next tier
        if not tier_client_team:
            print("There are no teachers left on this client's team, move to next group, add 1 :early")
            current_step += 1
            continue

        # randomly select staff from list
        i = randrange(0, len(tier_client_team))

        # find empty client hours
        items = client_sch.items()
        client_open_times = [item[0] for item in items if item[1] == 0]

        # check on staff's available hours
        # get schedule for selected staff memeber
        staff_sch = all_staff_sch[tier_client_team[i]].copy()

        # delete items in dictionary where staff is already scheduled
        dummy_list = [item for item in staff_sch.items()]
        for item in dummy_list:
            if item[1] != "":
                staff_sch.pop(item[0], None)

        staff_open_times = [int(times) for times in staff_sch.keys()]

        # remove times from the client's open time list if they are not in the staff's open times
        client_open_times = [time for time in client_open_times if time in staff_open_times]
        length = len(client_open_times)

        # schedule for a client defined 'block' of hours, or by one hour
        if length >= schedule_var:
            j = schedule_var
        elif length < schedule_var and length > 1:
            j = 2
        elif len(client_open_times) == 1:
            j = 1
        else:
            # this whole section is VERY confusing
            if current_step == 3:
                tier_client_team.remove(tier_client_team[i])
                if not tier_client_team:
                    print("There are no available t1, t2, t3  or sub staff left on this client's team")
                    break
                else:
                    continue
            else:
                print("There are no available staff at this tier, move up 1 :late")
                current_step += 1
                continue
        
        # update client and staff schedule dictionaries
        for k in range(j):
            client_sch[client_open_times[k]] = tier_client_team[i]
            all_staff_sch[tier_client_team[i]][client_open_times[k]] = client_name

    conn.close()
    return client_sch
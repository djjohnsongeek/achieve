import os
import sqlite3
import re

from flask import Flask
from flask import render_template, request, session, redirect, Response, jsonify
from sqlite3 import Error
from djlib import sanitize
from SQL import db_connect

# NOTE: need to replace single error page with ui feedback
# NOTE: need to make sure that POST requests with AJAX for the difference forms (Add, Remove, Update)
# NOTE: ensure sure times are "valid"

DB_URL = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"

# initialize app
app = Flask(__name__, static_folder="C:\\Users\\Johnson\\Documents\\Projects\\Achieve\\static")

# ensure auto reload, from CS50 staff
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached, from CS50 staff
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clients", methods=["GET", "POST"])
def clients():
    # for GET requests
    if request.method == "GET":
        db, conn = db_connect(DB_URL)
        db.execute("SELECT name FROM staff")
        staff_query = db.fetchall()
        db.execute("SELECT name FROM clients")
        client_query = db.fetchall()
        conn.close()
        return render_template("clients.html", staff_query=staff_query, client_query=client_query)

    # for POST Requests (adding client info) --
    # store client's name, check for no value
    
    if not request.form.get("client_name"):
        return render_template("error.html", message="Please provide the Client's name")
    client_name = request.form.get("client_name").strip()
   
    # store client hours, check for no value
    if not request.form.get("client_hours_start") or not request.form.get("client_hours_end"):
        return render_template("error.html", message=f"Please provide the {client_name}'s start and end times")
    
    client_hours_start = request.form.get("client_hours_start")
    client_hours_end = request.form.get("client_hours_end")

    # validate both times with regular expresssions:
    time = re.compile(r"[012][0-9]:[0-5][0-9]")
    if not time.match(client_hours_start) or not time.match(client_hours_end):
        return render_template("error.html", message="Start or End times are formatted incorrectly")

    # combine start and end times into one variable
    client_hours = client_hours_start + "-" + client_hours_end

    # prepare client info variables as a tuple
    client_info = (client_name, client_hours)

    # check to make sure at least one team member was assigend to client's team
    if not request.form.get("assign_teacher0") and not request.form.get("assign_teacher1") and not request.form.get("assign_teacher2") and not request.form.get("assign_teacher3"):
        return render_template("error.html", message=f"Please provide {client_name} with at least one Team Member")

    # create list of team members, remove variables that have no data
    t_members = [request.form.get("assign_teacher0"), request.form.get("assign_teacher1"), request.form.get("assign_teacher2"),
      request.form.get("assign_teacher3")]
    t_members[:] = [member for member in t_members if member]

    # remove duplicates
    unique_members = []
    for staff in t_members:
        if staff not in unique_members:
            unique_members.append(staff)

    # connect to database
    db, conn = db_connect(DB_URL)

    # check if client's name is already in the database
    db.execute("SELECT * FROM clients WHERE name=?", (client_name,))
    if db.fetchall():
        return render_template("error.html", message=f"{client_name} is already in the database")
    
    # insert data, or ignore if name is already present
    db.execute("INSERT INTO clients (name, hours) VALUES (?,?)", client_info) #NOTE: Test this site w/o JS to see if this line of code is working

    # Insert client IDs and Staff ID's into the data base
    for staff in unique_members:
        # get staff info
        db.execute("SELECT * FROM staff WHERE name=?", (staff,))
        staff_info = db.fetchone()

        # if no staff into is found, return error
        if not staff_info:
            return render_template("error.html", message=f"{staff} was not found in the staff database. New Client was not added")

        # insert staff ID and client ID into table "teams"
        else:
            # get client ID
            db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
            client_ID = db.fetchone()

            # TODO check if staff member is already on client's team?
            # insert client and staff ID into teams
            db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_ID["clientID"], staff_info["staffID"]))

    # commit and close database
    conn.commit()
    conn.close()
    return render_template("error.html", message="Success")

@app.route("/addclient", methods=["GET"])
def addclient():
    clientname = request.args.get("clientname").strip()
    
    # connect to database
    db, conn = db_connect(DB_URL)

    # check if client name is already in the database
    db.execute("SELECT name FROM clients WHERE name=?", (clientname,))
    query = db.fetchone()
    conn.close()

    # return true if name is not there, false if name is already there
    if not query:
        return jsonify(True)
    else:
        return jsonify(False)

@app.route("/clients/remove", methods=["POST"])
def remove_client():
    # validate remove_client form
    if not request.form.get("slct_client"):
        return render_template("error.html", message="Please provide the client name to be removed the database")
    client_name = request.form.get("slct_client")

    # connect to database
    db, conn = db_connect(DB_URL)

    # get clientID, check to see if client is in database
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    query = db.fetchone()
    if not query:
        return render_template("error.html", message=f"{client_name} was not found in the database")

    # delete client's team assignments, delete client
    db.execute("DELETE FROM teams where clientID=?", (query["clientID"],))
    db.execute("DELETE FROM clients WHERE name=?", (client_name,))

    # commit changes and close the connection, return success
    conn.commit()
    conn.close()
    return render_template("error.html", message="Success")

@app.route("/clients/update", methods=["POST"])
def update_client():
    
    if not request.form.get("update_client"):
        return render_template("error.html", message="Please provide the Client's name")

    client_name = request.form.get("update_client")

    # connect to db
    db, conn = db_connect(DB_URL)

    # check if client is in the data base
    db.execute("SELECT * FROM clients WHERE name=?", (client_name,))
    client_info = db.fetchone()
    if not client_info:
        return render_template("error.html", message=f"{client_name} was not found in the database")

    # check for incomplete hours data
    if not request.form.get("new_client_hours_start") and request.form.get("new_client_hours_end"):
        return render_template("error.html", message="Pleave provide both start and end times")
    if request.form.get("new_client_hours_start") and not request.form.get("new_client_hours_end"):
        return render_template("error.html", message="Pleave provide both start and end times")

    # get and insert new hours data
    if request.form.get("new_client_hours_start") and request.form.get("new_client_hours_end"):
        client_hours_start = request.form.get("new_client_hours_start")
        client_hours_end = request.form.get("new_client_hours_end")

        # ensure proper data format
        time = re.compile(r"[012][0-9]:[0-5][0-9]")
        if not time.match(client_hours_end) or not time.match(client_hours_start):
            return render_template("error.html", message="Incorrect time format")

        client_hours = client_hours_start + "-" + client_hours_end
        db.execute("UPDATE clients SET hours=? WHERE name=?", (client_hours, client_name))

    # if there is absent data
    if request.form.get("absent"):
        # ensure proper data format
        absent = request.form.get("absent")
        try:
            absent = int(absent)
        except ValueError:
            return render_template("error.html", message="Absent field must be a digit")

        if absent == 1 or absent == 0:
            # update client
            db.execute("UPDATE clients SET absent=? WHERE name=?", (absent, client_name))
        else:
            return render_template("error.html", message="Incorrect value for Absent/Present Radio Button")

    # get team placement
    new_teacher = request.form.get("new_teacher")
    add_or_remove = request.form.get("addOrRemove_teacher")

    # if there is data, 
    if new_teacher and add_or_remove:

        # check if selected staff is in the database
        db.execute("SELECT * FROM staff WHERE name=?", (new_teacher,))
        staff_info = db.fetchone()
        if not staff_info:
            return render_template("error.html", message=f"{new_teacher} was not found in the database")
        
        # check if teacher is already on client's team
        db.execute("SELECT * FROM teams WHERE clientID=? AND staffID=?", (client_info["clientID"], staff_info["staffID"]))
        team_info = db.fetchone()
        
        # check if data recieved matches expected pattern
        regex = re.compile(r"add|remove")
        result = regex.match(add_or_remove)

        if not result:
            return render_template("error.html", message="Incorrect Add/Remove data recieved")

        if add_or_remove == "add":
            if team_info:
                return render_template("error.html", message=f"{new_teacher} is already on {client_name}'s team")
            else:
                # add selected teacher to selected Client's team
                db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_info["clientID"], staff_info["staffID"]))

        if add_or_remove == "remove":
            if not team_info:
                return render_template("error.html", message=f"No removal necessary, {new_teacher} and {client_name} are not on the same team")
            else:
                # remove selected teacher from selected Client's team
                db.execute("DELETE FROM teams WHERE clientID=? and staffID=?", (client_info["clientID"], staff_info["staffID"]))

    # commit changes and return success message
    conn.commit()
    conn.close()
    return render_template("error.html", message="Success")

@app.route("/staff", methods=["POST", "GET"])
def staff():
    if request.method == "GET":
        # add in auto population of select fields
        # connect to database
        db, conn = db_connect(DB_URL)

        # retrieve all staff names
        db.execute("SELECT name FROM staff")
        staff_names = db.fetchall()

        # close connection to database
        conn.close()
        return render_template("staff.html", staff_names=staff_names)
    
    # check if staff field is filled out
    if not request.form.get("staff_name"):
        return render_template("error.html", message="Please provide staff's name")
    staff_name = request.form.get("staff_name").strip()

    # check if RBT field is filled out correctly
    if not request.form.get("RBT"):
        rbt_status = 0
    else:
        try:
            rbt_status = int(request.form.get("RBT"))
        except ValueError:
            return render_template("error.html", message="Incorrect value for RBT checkbox")

        if rbt_status != 1:
            return render_template("error.html", message="Incorrect value for RBT checkbox")
    
    
    # check Tier field is filled out
    if not request.form.get("Tier"):
        rbt_tier = 1

    else:
        try:
            rbt_tier = int(request.form.get("Tier"))
        except ValueError:
            return render_template("error.html", message="Incorrect value entered in to Tier radio button")
        if rbt_tier != 1 and rbt_tier != 2 and rbt_tier != 3:
            return render_template("error.html", message="Incorrect number value entered in to Tier radio button")

    # check if hours filed is filled out
    if not request.form.get("staff_hours_start") or not request.form.get("staff_hours_end"):
        return render_template("error.html", message="You must provide staff hours")
    
    # check hour data is in the correct format
    staff_hours_start = request.form.get("staff_hours_start")
    staff_hours_end = request.form.get("staff_hours_end")
    time = re.compile(r"[012][0-9]:[0-5][0-9]")
    if not time.match(staff_hours_start) or not time.match(staff_hours_end):
        return render_template("error.html", message="Incorrect time format")

    # built final start and end times
    staff_hours = staff_hours_start + "-" + staff_hours_end

    # connect to database
    db, conn = db_connect(DB_URL)

    # check if staff is in the database
    db.execute("SELECT * FROM staff WHERE name=?", (staff_name,))
    staff_info = db.fetchone()
    if staff_info:
        return render_template("error.html", message=f"{staff_name} is already in the database")
    
    # insert staff info into the database
    db.execute("INSERT INTO staff (name, rbt, tier, hours) VALUES(?,?,?,?)", (staff_name, rbt_status, rbt_tier, staff_hours))

    # close database
    conn.commit()
    conn.close()

    # return success
    return render_template("error.html", message="Success")

@app.route("/staff/remove", methods=["POST"])
def remove_staff():
    # check if staff name is filled out
    if not request.form.get("slct_staff_remove"):
        return render_template("error.html", message="Please choose a staff member to remove from the database")
    staff_name = request.form.get("slct_staff_remove")

    # connect to database
    db, conn = db_connect(DB_URL)

    # get staffID
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    staffID = db.fetchone()

    # check if staff name is in the database
    if not staffID:
        return render_template("error.html", message=f"{staff_name} is not in the database")

    # delete staff info
    db.execute("DELETE FROM staff WHERE name=?", (staff_name,))

    # delete teams info related to selected staff
    db.execute("DELETE FROM teams WHERE staffID=?", (staffID["staffID"],))

    # commit changes and close database
    conn.commit()
    conn.close()

    return render_template("error.html", message="Success")

@app.route("/staff/update", methods=["POST"])
def staff_update():
    # check that staff name is filled out
    if not request.form.get("slct_staff_update"):
        return render_template("error.html", message="Please provide staff's name")
    staff_name = request.form.get("slct_staff_update")
    
    # connect to db
    db, conn = db_connect(DB_URL)

    # check if staff name is in database
    db.execute("SELECT * FROM staff WHERE name=?", (staff_name,))
    staff_info = db.fetchone()
    if not staff_info:
        return render_template("error.html", message=f"{staff_name} is not in the database")

    # if RBT is checked, validate data and submit
    if request.form.get("rbt_update"):
        try:
            rbt_status = int(request.form.get("rbt_update"))
        except ValueError:
            return render_template("error.html", message="RBT field must be a digits")
        
        if rbt_status == 1:
            db.execute("UPDATE staff SET rbt=? WHERE name=?", (rbt_status, staff_name))
        else:
            return render_template("error.html", message="Incorrect value for RBT field")

    # if Tier radio is chosen
    if request.form.get("tier_update"):
        try:
            tier = int(request.form.get("tier_update"))
        except ValueError:
            return render_template("error.html", message="Tier field must be a digit")
        
        if tier == 1 or tier == 2 or tier == 3:
            db.execute("UPDATE staff SET tier=? WHERE name=?", (tier, staff_name))
        else:
            return render_template("error.html", message="Incorrect value in Tier field")

    # if only one time field is filled out
    if request.form.get("staff_hours_update_start") and not request.form.get("staff_hours_update_end"):
        return render_template("error.html", message="Please provide both start and end times")

    if not request.form.get("staff_hours_update_start") and request.form.get("staff_hours_update_end"):
        return render_template("error.html", message="Please provide both start and end times")

    # if hours is filled out
    if request.form.get("staff_hours_update_start") and request.form.get("staff_hours_update_end"):

        hours_start = request.form.get("staff_hours_update_start")
        hours_end = request.form.get("staff_hours_update_end")

        time = re.compile(r"[012][0-9]:[0-5][0-9]")
        if time.match(hours_start) and time.match(hours_end):
            hours = hours_start + "-" + hours_end
            db.execute("UPDATE staff SET hours=? WHERE name=?", (hours, staff_name))
        else:
            return render_template("error.html", message="Incorrect time format")

    # if absent is chosen
    if request.form.get("staff_absent"):
        try:
            absent = int(request.form.get("staff_absent"))
        except ValueError:
            return render_template("error.html", message="Absent/Present field must be a digit")

        if absent == 1 or absent == 0:  
            db.execute("UPDATE staff SET absent=? WHERE name=?", (absent, staff_name))
        else:
            return render_template("error.html", message="Incorrect value in Absent/Present field")

    # close database and save changes
    conn.commit()
    conn.close()
    return render_template("error.html", message="Success")

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if request.method == "GET":
        return render_template("schedule.html")

    # if post request is sent
    print("Generating Schedule")
    return render_template("error.html", message="DONE")
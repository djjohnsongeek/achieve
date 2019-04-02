import os
import sqlite3
import re

from flask import Flask
from flask import render_template, request, session, redirect, Response, jsonify
from sqlite3 import Error
from djlib import sanitize
from SQL import db_connect

# Terminal Commands:
# initialize venv "  venv\Scripts\activate  "
# initialize app "  $env:FLASK_APP="achieve.py"
# developer mode "  $env:FLASK_ENV="developement"
# run with "flask run"

DB_URL = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"

# initialize app
app = Flask(__name__, static_folder="C:\\Users\\Johnson\\Documents\\Projects\\Achieve\\static")

# ensure auto reload
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
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

    # for POST Requests (adding client info) --NOTE: need to make sure that POST request for the difference forms (Add, Remove, Update) are delt with differently
    # store client's name, check for no value -NOTE: ensure proper data format (regular expressions or stripping white space(TODO)
    
    if not request.form.get("client_name"):
        return render_template("error.html", message="Please provide the Client's name")
    client_name = request.form.get("client_name").strip()
    
    # regular expressions
    names = re.compile(r"[a-zA-Z]\s[a-zA]")
    
    result = names.match(client_name)
    print(result)
    
    # store client hours, check for no value
    
    if not request.form.get("client_hours"):
        return render_template("error.html", message="Please provide the client's hours")
    client_hours = request.form.get("client_hours").strip()

    # prepare client info variables as a tuple
    client_info = (client_name, client_hours)

    # check to make sure at least one team member was assigend to client's team
    if not request.form.get("assign_teacher0") and not request.form.get("assign_teacher1") and not request.form.get("assign_teacher2") and not request.form.get("assign_teacher3"):
        return render_template("error.html", message="Please provide client with at least one Team Member")

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

    # insert data, or ignore if name is already present
    db.execute("INSERT OR IGNORE INTO clients (name, hours) VALUES (?,?)", client_info)

    # check if team members exist
    for staff in unique_members:
        db.execute("SELECT * FROM staff WHERE name=?", (staff,))
        staff_info = db.fetchone()
        # if one does not exits, return warning
        if not staff_info:
            return render_template("error.html", message=f"{staff} was not found in the staff database. New Client was not added")
        # if they exist, insert staff ID and client ID into table "teams"
        else:
            db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
            client_ID = db.fetchone()

            # check if staff member is already on client's team
            db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_ID["clientID"], staff_info["staffID"]))

    # commit and close database, render success message NOTE: to be changed
    conn.commit()
    conn.close()
    return render_template("error.html", message="Success")

@app.route("/addclient", methods=["GET"])
def addclient():
    clientname = request.args.get("clientname").strip()
    # ensure proper data format (TODO)
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
        return render_template("error.html", message="Please provide the client name to remove from the database")
    client_name = request.form.get("slct_client")
    # ensure proper data format (TODO)

    # connect to database
    db, conn = db_connect(DB_URL)

    # get clientID, check to see if client is in database
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    query = db.fetchone()
    if not query:
        return render_template("error.html", message="No client with this name was found in the database")

    # delete all rows in team table matching client ID
    db.execute("DELETE FROM teams where clientID=?", (query["clientID"],))

    # delete client from client table
    db.execute("DELETE FROM clients WHERE name=?", (client_name,))

    # commit changes and close the connection
    conn.commit()
    conn.close()
    # render success page NOTE: change this to a legit message later
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
        return render_template("error.html", message="No client with this name was found in the database")

    # get and insert new hours data
    client_hours = request.form.get("txt_new_client_hours")
    if client_hours:
        # ensure proper data format (TODO)
        db.execute("UPDATE clients SET hours=? WHERE name=?", (client_hours, client_name))
        
    # if there is absent data
    if request.form.get("absent"):
        # ensure proper data format (TODO)
        absent = int(request.form.get("absent"))
        # update client
        db.execute("UPDATE clients SET absent=? WHERE name=?", (absent, client_name))

    # get team placement
    new_teacher = request.form.get("new_teacher")
    add_or_remove = request.form.get("addOrRemove_teacher")

    # if there is data, 
    if new_teacher and add_or_remove:
        # ensure proper data format (TODO)

        # check if selected staff is in the database
        db.execute("SELECT * FROM staff WHERE name=?", (new_teacher,))
        staff_info = db.fetchone()
        if not staff_info:
            return render_template("error.html", message=f"{new_teacher} was not found in the database")
        
        # check if teacher is already on client's team
        db.execute("SELECT * FROM teams WHERE clientID=? AND staffID=?", (client_info["clientID"], staff_info["staffID"]))
        team_info = db.fetchone()
        
        if add_or_remove == "add":
            if team_info:
                return render_template("error.html", message=f"{new_teacher} is already on {client_name}'s team")

            # add selected teacher to selected Client's team
            db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_info["clientID"], staff_info["staffID"]))

        if add_or_remove == "remove":
            if not team_info:
                return render_template("error.html", message=f"No removal necessary, {new_teacher} and {client_name} are not on the same team")

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

    # check if RBT field is filled out
    if not request.form.get("RBT"):
        rbt_status = 0
    else:
        rbt_status = int(request.form.get("RBT"))
    
    # check Tier field is filled out
    if not request.form.get("Tier"):
        rbt_tier = 1
    else:
        rbt_tier = int(request.form.get("Tier"))

    # check if hours filed is filled out
    if not request.form.get("staff_hours"):
        return render_template("error.html", message="You must provide staff hours")
    staff_hours = request.form.get("staff_hours")

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
        return render_template(f"{staff_name} is not in the database")

    # if all fields are filled out (shortcut)
    if request.form.get("rbt_update") and request.form.get("tier_update") and request.form.get("staff_hours_update") and request.form.get("staff_absent"):
        rbt_status = int(request.form.get("rbt_update"))
        tier = int(request.form.get("tier_update"))
        hours = request.form.get("staff_hours_update").strip()
        absent = int(request.form.get("staff_absent"))

        # submit info in one query
        db.execute("UPDATE staff SET rbt=?, tier=?, hours=?, absent=? WHERE name=?", (rbt_status, tier, hours, absent, staff_name))

        # close and commit db
        conn.commit()
        conn.close()
        return render_template("error.html", message="Success, short cut")
        
    # if RBT is checked
    if request.form.get("rbt_update"):
        rbt_status = int(request.form.get("rbt_update"))
        db.execute("UPDATE staff SET rbt=? WHERE name=?", (rbt_status, staff_name))

    # if Tier radio is chosen
    if request.form.get("tier_update"):
        tier = int(request.form.get("tier_update"))
        db.execute("UPDATE staff SET tier=? WHERE name=?", (tier, staff_name))

    # if hours is filled out
    if request.form.get("staff_hours_update"):
        hours = request.form.get("staff_hours_update").strip()
        # ensure data is formatted correctly
            # (TODO)
        db.execute("UPDATE staff SET hours=? WHERE name=?", (hours, staff_name))
    
    # if absent is chosen
    if request.form.get("staff_absent"):
        absent = int(request.form.get("staff_absent"))
        db.execute("UPDATE staff SET absent=? WHERE name=?", (absent, staff_name))

    # close database and save changes
    conn.commit()
    conn.close()
    return render_template("error.html", message="Success")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")
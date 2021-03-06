import os
import sys
import sqlite3
import re
import csv
import pyAesCrypt

from flask import Flask
from flask import render_template, request, session, redirect, Response, jsonify, json, send_from_directory, flash
from sqlite3 import Error
from random import randrange
from werkzeug.security import check_password_hash, generate_password_hash
from jinja2 import Environment, FileSystemLoader

from SQL import db_connect, db_backup, db_restore
from server import generate_schedules, convert_strtime, create_schhours, login_required, shorten_day, lengthen_day, admin_required
from cypher import scramble, unscramble

# NOTE: need to review code, optimize and improve design and style, use custom fuctions as well as revamp comments

"""
Achieve allows users to add, edit and remove staff and client information to and from database.
From the '/schedule' route it generates a daily schedule and saves it as an csv file which can be downloaded.
(The 'generate schedule' is still in progress, and 'download csv file' is yet to be implemented)
"""
DB_PATH = sys.path[0] + "\\achieve.db"

# initialize app
app = Flask(__name__, instance_path=sys.path[0] + "\\protected")
app.secret_key = "development"

# ensure auto reload, code from CS50 staff
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached, code from CS50 staff
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
        
    if request.method == "GET":
        return render_template("login.html")

    # remove anyone logged in already
    session.clear()
    session["logged_in"] = False

    if request.method == "POST":

        # setup feedback for errors
        session["error"] = 1

        # check if all fields are filled out
        if not request.form.get("username"):
            flash("You must provide a username")
            return redirect("/login")

        if not request.form.get("password"):
            flash("You must provide a password")
            return redirect("/login")

        # get user id number
        db, conn = db_connect(DB_PATH)
        db.execute("SELECT * FROM users WHERE username=?", (request.form.get("username"),))
        user_id = db.fetchone()

        # check username/password is valid
        if not user_id or not check_password_hash(user_id["password"], request.form.get("password")):
            flash("Username or Password is not valid")
            return redirect("/login")

        # update session
        session["user_id"] = user_id["userID"]
        session["logged_in"] = True
        conn.close()

        # redirect user to index, setup feedback for info
        session["error"] = 0
        flash("Logged In")
        return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    session["logged_in"] = False
    session["error"] = 0
    flash("Logged Out")
    return redirect("/login")

@app.route("/changepw", methods=["POST", "GET"])
@login_required
def changepw():

    if request.method == "GET":
        return render_template("changepw.html")

    # setup feedback for errors
    session["error"] = 1

    # check if all fields are filled out
    if not request.form.get("password_new"):
        flash("You must provide a new password")
        return redirect("/changepw")

    pw_new = request.form.get("password_new")

    if not request.form.get("password_check"):
        flash("You must re-enter your new password")
        return redirect("/changepw")
    
    pw_check = request.form.get("password_check")

    # check that the two password fields match
    if pw_check != pw_new:
        flash("Passwords do not match")
        return redirect("/changepw")

    # hash and update password
    hashed_pw = generate_password_hash(pw_new, method="sha256", salt_length=8)
    db, conn = db_connect(DB_PATH)

    db.execute("SELECT username FROM users WHERE userID=?", (session["user_id"],))
    user_name = db.fetchone()
    db.execute("UPDATE users SET password=? WHERE username=?", (hashed_pw, user_name["username"]))
    conn.commit()
    conn.close()

    # redirect user to index, change feedback from errors to info
    session["error"] = 0
    flash("Password Changed")
    return redirect("/")

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/clients", methods=["GET", "POST"])
@login_required
@admin_required
def clients():
    # for GET requests
    if request.method == "GET":
        db, conn = db_connect(DB_PATH)
        db.execute("SELECT name FROM staff")
        staff_query = db.fetchall()
        db.execute("SELECT name FROM clients")
        client_query = db.fetchall()
        conn.close()
        return render_template("clients.html", staff_query=staff_query, client_query=client_query, unscramble=unscramble)

    # for POST Requests (adding client info)
    # store client's name, check for no value
    session["error"] = 1

    if not request.form.get("client_name"):
        flash("Please provide the Client's name")
        return redirect("/clients")

    client_name = request.form.get("client_name").strip()
   
    # store client hours, check for no value
    if not request.form.get("client_hours_start") or not request.form.get("client_hours_end"):
        flash(f"Please provide {client_name}'s start and end times")
        return redirect("/clients")
    
    client_hours_start = request.form.get("client_hours_start")
    client_hours_end = request.form.get("client_hours_end")

    # validate both times with regular expresssions:
    time = re.compile(r"[012][0-9]:30")
    if not time.match(client_hours_start) or not time.match(client_hours_end):
        flash("Start or End times are formatted incorrectly")
        return redirect("/clients")

    # build final start and end times, build scheduable hours
    client_hours = client_hours_start + "-" + client_hours_end
  
    # generate a list of the staff's scheduable hours
    total_hours = len(create_schhours(client_hours))

    # prepare client info variables as a tuple
    client_name = scramble(client_name)
    client_info = [client_name, total_hours]

    # store client attendance days, and hours
    client_attendance = []
    client_hours_list = []
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:

        if request.form.get(day) != day and request.form.get(day) != None:
            flash("Invalid day data submitted")
            return redirect("/clients")
        
        if request.form.get(day) == day:
            client_attendance.append(1)
            client_hours_list.append(client_hours)
        else:
            client_attendance.append(0)
            client_hours_list.append(None)

    client_info = client_info + client_attendance

    # create list of team members, remove variables that have no data
    t_members = [request.form.get("assign_teacher0"), request.form.get("assign_teacher1"), request.form.get("assign_teacher2"),
      request.form.get("assign_teacher3")]
    t_members[:] = [member for member in t_members if member]

    # check to make sure at least one team member was assigned to client's team 
    # if len(t_members) == 0:
    #     flash(f"Please provide {unscramble(client_name)} with at least one Team Member")
    #     return redirect("/clients")

    # remove duplicates
    unique_members = set(t_members)
    
    # connect to database
    db, conn = db_connect(DB_PATH)

    # check if client's name is already in the database
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    if db.fetchone():
        flash(f"{unscramble(client_name)} is already in the database. If you want to edit Client information please use the Update Client Info form")
        return redirect("/clients")

    print(client_info)
    # insert client info, uses default color
    # NOTE: Test this site w/o JS to see if this line of code is working
    db.execute("INSERT INTO clients (name, totalhours, mon, tue, wed, thu, fri) VALUES (?,?,?,?,?,?,?)", client_info) 
    conn.commit()

    # get client ID (that now should exist)
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    client_info = db.fetchone()

    # add on client ID to client hours list
    client_hours_list.insert(0, client_info["clientID"])

    # insert client schedule data into data base
    db.execute("INSERT INTO clienthours (clientID, monday, tuesday, wednesday, thursday, friday) VALUES(?,?,?,?,?,?)", client_hours_list)

    # check for client classification information
    if request.form.get("color"):
        try:
            category = int(request.form.get("color"))
        except ValueError:
            flash("Incorrect client classification input")
            return redirect("/clients")

        if category not in {1,2,3}:
            flash("Incorrect client classification input")
            return redirect("/clients")
        else:
            db.execute("UPDATE clients SET color=? WHERE clientID=?", (category, client_info["clientID"]))

    # Insert teams data
    for staff in unique_members:
        # get staff info
        db.execute("SELECT staffID FROM staff WHERE name=?", (staff,)) #bug?
        staff_info = db.fetchone()

        # check to make sure staff exists
        if not staff_info:
            flash(f"{staff} was not found in the staff database. New Client was not added to their team")
            return redirect("/clients")

        # insert staff ID and client ID into table "teams"
        else:
            # insert client and staff ID into teams
            db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_info["clientID"], staff_info["staffID"]))

    # commit and close database
    conn.commit()
    conn.close()

    # provide user feedback
    session["error"] = 0
    flash("Client Successfully Added")
    return redirect("/clients")

@app.route("/clients/remove", methods=["POST"])
def remove_client():
    # setup feedback as error
    session["error"] = 1

    # validate remove_client form
    if not request.form.get("slct_client"):
        flash("Please provide the client name to be removed")
        return redirect("/clients")

    client_name = request.form.get("slct_client")

    # connect to database
    db, conn = db_connect(DB_PATH)

    # get clientID, check to see if client is in database
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    query = db.fetchone()
    if not query:
        flash(f"{unscramble(client_name)} was not found in the database")
        return redirect("/clients")

    # delete client's team assignments, delete client
    db.execute("DELETE FROM teams where clientID=?", (query["clientID"],))
    db.execute("DELETE FROM clients WHERE clientID=?", (query["clientID"],))
    db.execute("DELETE FROM clienthours WHERE clientID=?", (query["clientID"],))

    # commit changes and close the connection, return success
    conn.commit()
    conn.close()

    # change feed back to info
    session["error"] = 0
    flash(f"{unscramble(client_name)} has been deleted")
    return redirect("clients")

@app.route("/clients-update", methods=["GET", "POST"])
@login_required
@admin_required
def update_client():
    # GET requests
    if request.method == "GET":
        db, conn = db_connect(DB_PATH)
        db.execute("SELECT name FROM staff")
        staff_query = db.fetchall()
        db.execute("SELECT name FROM clients")
        client_query = db.fetchall()
        conn.close()
        return render_template("clients-update.html", staff_query=staff_query, client_query=client_query, unscramble=unscramble)

    # POST requests
    # setup feedback for errors
    session["error"] = 1

    # ensure client name is filled out
    if not request.form.get("update_client"):
        flash("Please provide a client's name")
        return redirect("/clients-update")

    client_name = request.form.get("update_client")

    # connect to db
    db, conn = db_connect(DB_PATH)

    # check if client is in the data base
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    client_info = db.fetchone()
    if not client_info:
        flash(f"{unscramble(client_name)} was not found in the database")
        return redirect("/clients-update")

    # get and insert new hours data
    if request.form.get("new_client_hours_start") and request.form.get("new_client_hours_end"):

        client_hours_start = request.form.get("new_client_hours_start")
        client_hours_end = request.form.get("new_client_hours_end")

        # ensure proper data format
        time = re.compile(r"[012][0-9]:30")
        if not time.match(client_hours_end) or not time.match(client_hours_start):
            flash("Invalid time format")
            return redirect("/clients-update")

        # get client's total number of hours
        client_hours = client_hours_start + "-" + client_hours_end
        total_hours = len(create_schhours(client_hours))
        
        # store client hours
        client_days = []
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            # validate day data
            if request.form.get(day) != day and request.form.get(day) != None:
                flash("Invalid day data")
                return redirect("/clients-update")

            if request.form.get(day) == day:
                client_days.append(day)
            
        db.execute("UPDATE clients SET totalhours=? WHERE clientID=?", (total_hours, client_info["clientID"]))
        for item in client_days:
            db.execute(f"UPDATE clienthours SET {item}=? WHERE clientID=?", (client_hours, client_info["clientID"]))

    # get and insert new attendance data
    client_att = []
    for day in ["mon", "tue", "wed", "thu", "fri"]:
        try:
            if request.form.get(day) != None and int(request.form.get(day)) not in {0, 1}:
                flash("Invalid attendance data")
                return redirect("/clients-update")
        except ValueError:
            flash("Invalid attendance data")
            return redirect("/clients-update")

        # skip over fields with no info seleected
        if not request.form.get(day):
            continue

        if int(request.form.get(day)) == 1:
            client_att.append([day, 1])
        if int(request.form.get(day)) == 0:
            client_att.append([day, 0])

    # get delete hours checkbox
    if not request.form.get("del_hours"):
        del_hours = False
    else:
        del_hours = True

    # insert data into database
    for item in client_att:
        full_day = lengthen_day(item[0])

        if del_hours and item[1] == 0:
            db.execute(f"UPDATE clienthours SET {full_day}=Null WHERE clientID=?", (client_info["clientID"],))

        # get client's housr info for each day
        db.execute(f"SELECT {full_day} FROM clienthours WHERE clientID=?", (client_info["clientID"],))
        result = db.fetchone()

        # return an error if client is marked present on days where they have no hours
        if not result[full_day] and item[1] == 1:
            flash("Client cannot be marked present if they have no scheduable hours for that day")
            return redirect("/clients-update")

        # update the data
        item[0] = shorten_day(item[0])
        db.execute(f"UPDATE clients SET {item[0]}=? WHERE clientID=?", (item[1], client_info["clientID"]))

    # change client's color classification if needed
    if request.form.get("update_color"):
        try:
            update_color = int(request.form.get("update_color"))
        except ValueError:
            flash("Invalid client classification data")
            return redirect("/clients-update")

        if update_color not in {1, 2, 3}:
            flash("Invalid client classification data")
            return redirect("/clients-update")
        else:
            db.execute("UPDATE clients SET color=? WHERE name=?", (update_color, client_name))

    # get team placement
    new_teacher = request.form.get("new_teacher")
    add_or_remove = request.form.get("addOrRemove_teacher")

    # if there is data, 
    if new_teacher and add_or_remove:

        # check if selected staff is in the database
        db.execute("SELECT * FROM staff WHERE name=?", (new_teacher,))
        staff_info = db.fetchone()
        if not staff_info:
            flash(f"{new_teacher} was not found in the database")
            return redirect("/clients-update")
        
        # check if teacher is already on client's team
        db.execute("SELECT * FROM teams WHERE clientID=? AND staffID=?", (client_info["clientID"], staff_info["staffID"]))
        team_info = db.fetchone()
        
        # check if data recieved matches expected pattern
        regex = re.compile(r"add|remove")
        result = regex.match(add_or_remove)

        if not result:
            flash("Invalid Add or Remove data")
            return redirect("/clients-update")

        if add_or_remove == "add":
            if team_info:
                flash(f"{new_teacher} is already on {unscramble(client_name)}'s team")
                return redirect("/clients-update")
            else:
                # add selected teacher to selected Client's team
                db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_info["clientID"], staff_info["staffID"]))

        if add_or_remove == "remove":
            if not team_info:
                flash(f"No removal necessary: {new_teacher} and {unscramble(client_name)} are not on the same team")
                return redirect("/clients-update")
            else:
                # remove selected teacher from selected Client's team
                db.execute("DELETE FROM teams WHERE clientID=? and staffID=?", (client_info["clientID"], staff_info["staffID"]))

    # commit changes, change feedback style to info
    conn.commit()
    conn.close()

    session["error"] = 0
    flash(f"{unscramble(client_name)}'s info has been updated")
    return redirect("/clients-update")

@app.route("/addclient", methods=["GET"])
def addclient():
    clientname = scramble(request.args.get("clientname"))
    
    # connect to database
    db, conn = db_connect(DB_PATH)

    # check if client name is already in the database
    db.execute("SELECT clientID FROM clients WHERE name=?", (clientname,))
    query = db.fetchone()
    conn.close()

    # return result
    if query:
        return jsonify(True)
    else:
        return jsonify(False)

@app.route("/clients/view-client-info")
@login_required
@admin_required
def view_clients():
    db, conn = db_connect(DB_PATH)

    # get basic client info
    db.execute("SELECT name, totalhours, color FROM clients ORDER BY name DESC")
    client_info = [dict(row) for row in db.fetchall()]


    # update number data with text, decrypt client name
    for row in client_info:
        if row["color"] == 1:
            row["color"] = "Green"
        elif row["color"] == 2:
            row["color"] = "Yellow"
        else:
            row["color"] = "Red"

        row["name"] = unscramble(row["name"])

    # get team information
    db.execute("SELECT clients.name, staff.name FROM teams JOIN staff ON staff.staffID=teams.staffID JOIN clients ON clients.clientID=teams.clientID ORDER BY clients.name DESC")

    # convert to dictionary of teams by client
    team = []
    team_dict = {}
    for row in db.fetchall():
        item = list(row)
        item[0] = unscramble(item[0])

        if item[0] not in team_dict.keys():  
            team = []

        if item[1] not in team:
            team.append(item[1])
            team_dict[item[0]] = team

    # close database and render client tables
    conn.close()
    return render_template("view-client-info.html", client_info = client_info, client_teams = team_dict)

@app.route("/clients/view-client-hours")
@login_required
@admin_required
def view_client_hrs():
    db, conn = db_connect(DB_PATH)

    # get client hours, decrypt client name
    db.execute("SELECT clients.name, monday, tuesday, wednesday, thursday, friday FROM clienthours JOIN clients ON clienthours.clientID = clients.clientID ORDER BY clients.name DESC")
    client_hours = [dict(row) for row in db.fetchall()]
    for row in client_hours:
        row["name"] = unscramble(row["name"])

    # close database and render client tables
    conn.close()
    return render_template("view-client-hours.html", client_hours = client_hours)

@app.route("/clients/view-client-att")
@login_required
@admin_required
def view_client_att():
    db, conn = db_connect(DB_PATH)

    # get client attendance data, decrypt client name
    db.execute("SELECT name, mon, tue, wed, thu, fri FROM clients ORDER BY name DESC")
    client_att = [dict(row) for row in db.fetchall()]

    for row in client_att:
        for day in ["mon", "tue", "wed", "thu", "fri"]:
            if row[day] == 1:
                row[day] = "Present"
            else:
                row[day] = "OUT"

        row["name"] = unscramble(row["name"])

    # close database and render client tables
    conn.close()
    return render_template("view-client-att.html", client_att = client_att)

@app.route("/staff", methods=["POST", "GET"])
@login_required
@admin_required
def staff():
    if request.method == "GET":
        # connect to database
        db, conn = db_connect(DB_PATH)

        # retrieve all staff names
        db.execute("SELECT name FROM staff")
        staff_names = db.fetchall()

        # close connection to database
        conn.close()
        return render_template("staff.html", staff_names=staff_names)
    
    # process POST data
    # setup feedback for errors
    session["error"] = 1

    # check if staff field is filled out
    if not request.form.get("staff_name"):
        flash("Please provide staff's name")
        return redirect("/staff")

    staff_name = request.form.get("staff_name").strip()

    # check if RBT field is filled out correctly
    if not request.form.get("RBT"):
        rbt_status = 0
    else:
        try:
            rbt_status = int(request.form.get("RBT"))
        except ValueError:
            flash("Incorrect value for RBT checkbox")
            return redirect("/staff")

        if rbt_status != 1:
            flash("Incorrect value for RBT checkbox")
            return redirect("/staff")
    
    # check Tier field is filled out
    if not request.form.get("Tier"):
        rbt_tier = 1
    else:
        try:
            rbt_tier = int(request.form.get("Tier"))
        except ValueError:
            flash("Incorrect value entered in to Tier radio button")
            return redirect("/staff")
        if rbt_tier not in {1,2,3}:
            flash("Incorrect value entered in to Tier radio button")
            return redirect("/staff")
    
    if rbt_status == 0:
        rbt_tier = 0
        color = 1
    else:
        color = rbt_tier
    # check if hours field is filled out
    if not request.form.get("staff_hours_start") or not request.form.get("staff_hours_end"):
        flash("You must provide staff start and end times")
        return redirect("/staff")
    
    # check hour data is in the correct format
    staff_hours_start = request.form.get("staff_hours_start")
    staff_hours_end = request.form.get("staff_hours_end")
    time = re.compile(r"[012][0-9]:30")
    if not time.match(staff_hours_start) or not time.match(staff_hours_end):
        flash("Incorrect time format")
        return redirect("/staff")

    # built final start and end times
    staff_hours = staff_hours_start + "-" + staff_hours_end

    #build staff attendance/hours
    staff_att = []
    staff_hours_list = []
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        if request.form.get(day) != day and request.form.get(day) != None:
            flash("Invalid day data")
            return redirect("/staff")

        if request.form.get(day) == day:
            staff_hours_list.append(staff_hours)
            staff_att.append(1)

        else:
            staff_hours_list.append(None)
            staff_att.append(0)

    # connect to database
    db, conn = db_connect(DB_PATH)

    # check if staff is in the database
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    if db.fetchone():
        flash(f"{staff_name} is already in the database")
        return redirect("/staff")
    
    # insert staff info into the database
    staff_info = [staff_name, rbt_status, rbt_tier, color] + staff_att
    db.execute("INSERT INTO staff (name, rbt, tier, color, mon, tue, wed, thu, fri) VALUES(?,?,?,?,?,?,?,?,?)", (staff_info))

    # get staffID to save staff hours
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    staff_ID = db.fetchone()
    staff_hours_list.insert(0, staff_ID["staffID"])
    db.execute("INSERT INTO staffhours (staffID, monday, tuesday, wednesday, thursday, friday) VALUES(?,?,?,?,?,?)", staff_hours_list)

    # commit and close database
    conn.commit()
    conn.close()

    # return success, update feedback to info
    session["error"] = 0
    flash(f"{staff_name} Succesfully Added")
    return redirect("/staff")

@app.route("/staff/remove", methods=["POST"])
def remove_staff():

    # prepare feedback for errors
    session["error"] = 1

    # check if staff name is filled out
    if not request.form.get("slct_staff_remove"):
        flash("Please choose a staff member to remove from the database")
        return redirect("/staff")

    staff_name = request.form.get("slct_staff_remove")

    # connect to database
    db, conn = db_connect(DB_PATH)

    # get staffID, check to make sure it is in the database
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    staff_ID = db.fetchone()
    if not staff_ID:
        flash(f"{staff_name} is not in the database")
        return redirect("/staff")

    # delete staff info
    db.execute("DELETE FROM staff WHERE staffID=?", (staff_ID["staffID"],))
    db.execute("DELETE FROM teams WHERE staffID=?", (staff_ID["staffID"],))
    db.execute("DELETE FROM staffhours WHERE staffID=?", (staff_ID["staffID"],))

    # remove staff name from classroom teacher or sublist
    db.execute("SELECT classroom FROM classrooms")
    classrooms = db.fetchall()
    for classroom in classrooms:
        db.execute("SELECT teacher1, teacher2, sub1, sub2, sub3, sub4 FROM classrooms WHERE classroom=?", (classroom["classroom"],))
        teachers = db.fetchone()
        for key in teachers.keys():
            if teachers[key] == staff_name:
                db.execute(f"UPDATE classrooms SET {key}=? WHERE classroom=?", (None, classroom["classroom"]))

    # commit changes and close database
    conn.commit()
    conn.close()
    
    # change feedback to info
    session["error"] = 0
    flash(f"{staff_name} has been deleted")
    return redirect("/staff")

@app.route("/staff-update", methods=["GET", "POST"])
@login_required
@admin_required
def update_staff():
    # ---GET requests---
    if request.method == "GET":
        # connect to database
        db, conn = db_connect(DB_PATH)

        # retrieve all staff names
        db.execute("SELECT name FROM staff")
        staff_names = db.fetchall()

        # close connection to database
        conn.close()
        return render_template("staff-update.html", staff_names=staff_names)

    # ---POST requests---
    # prepare feedback for errors
    session["error"] = 1

    # check that staff name is filled out
    if not request.form.get("slct_staff_update"):
        flash("Please provide a staff member's name")
        return redirect("/staff-update")

    staff_name = request.form.get("slct_staff_update")
    
    # connect to db
    db, conn = db_connect(DB_PATH)

    # check if staff name is in database
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    staff_info = db.fetchone()
    if not staff_info:
        flash(f"{staff_name} is not in the database")
        return redirect("/staff-update")

    # if RBT is checked, validate data and submit
    if request.form.get("rbt_update"):
        try:
            rbt_status = int(request.form.get("rbt_update"))
        except ValueError:
            flash("RBT field must be a digit")
            return redirect("/staff")
        
        if rbt_status == 1:
            db.execute("UPDATE staff SET rbt=? WHERE staffID=?", (rbt_status, staff_info["staffID"]))
        else:
            flash("Incorrect value for RBT field")
            return redirect("/staff-update")

    # if Tier radio is chosen
    if request.form.get("tier_update"):
        try:
            tier = int(request.form.get("tier_update"))
        except ValueError:
            flash("Teacher tier field must be a digit")
            return redirect("/staff-update")
        
        if tier in {1,2,3}:
            db.execute("UPDATE staff SET tier=?, color=? WHERE staffID=?", (tier, tier, staff_info["staffID"]))
        else:
            flash("Invalid teacher tier data")
            return redirect("/staff-update")

    # build hours variable
    if request.form.get("staff_hours_update_start") and request.form.get("staff_hours_update_end"):

        # build final start and end times
        hours_start = request.form.get("staff_hours_update_start")
        hours_end = request.form.get("staff_hours_update_end")

        # check for correct time format
        time = re.compile(r"[012][0-9]:30")
        if time.match(hours_start) and time.match(hours_end):

            staff_hours = hours_start + "-" + hours_end
            staff_days = []
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                if request.form.get(day) != day and request.form.get(day) != None:
                    flash("Invalid day data")
                    return redirect("/staff-update")

                if request.form.get(day) == day:
                    staff_days.append(day)

            for items in staff_days:
                db.execute(f"UPDATE staffhours SET {items}=? WHERE staffID=?", (staff_hours, staff_info["staffID"]))

        else:
            flash("Invalid time format")
            return redirect("/staff-update")

    # staff color category
    if request.form.get("staff_color"):
        try:
            color = int(request.form.get("staff_color"))
        except ValueError:
            flash("Invalid staff classification value")
            return redirect("/staff-update")

        if color not in {1,2,3}:
            flash("Invalid staff classification value")
            return redirect("/staff-update")
        else:
            db.execute("UPDATE staff SET color=? WHERE staffID=?", (color, staff_info["staffID"]))

    # prepare staff attendance variables
    staff_att = []
    for day in ["mon", "tue", "wed", "thu", "fri"]:
        try:
            if request.form.get(day) != None and int(request.form.get(day)) not in {0,1}:
                flash("Invalid attendance data")
                return redirect("/staff-update")

        except ValueError:
            flash("Invalid attendance data")
            return redirect("/staff-update")

        if not request.form.get(day):
            continue
        
        if int(request.form.get(day)) == 1:
            staff_att.append([day, 1])
        else:
            staff_att.append([day, 0])

    # get delete hours checkbox
    if not request.form.get("del_hours"):
        del_hours = False
    else:
        del_hours = True

    # update database with new attendance data
    for item in staff_att:
        full_day = lengthen_day(item[0])

        # remove hours data completely where staff is absent
        if del_hours and item[1] == 0:
            db.execute(f"UPDATE staffhours SET {full_day}=Null WHERE staffID=?", (staff_info["staffID"],))

        # check that staff member actually has hours
        db.execute(f"SELECT {full_day} FROM staffhours WHERE staffID=?", (staff_info["staffID"],))
        result = db.fetchone()

        # return error if staff is to be marked present on a day they have no hours
        if not result[full_day] and item[1] == 1:
            flash("Staff info not updated: Staff cannot be marked present if they have no scheduable hours for that day")
            return redirect("/staff-update")

        item[0] = shorten_day(item[0])
        db.execute(f"UPDATE staff SET {item[0]}=? WHERE staffID=?", (item[1], staff_info["staffID"]))

    # close database and save changes
    conn.commit()
    conn.close()

    # prepare feedback info
    session["error"] = 0
    flash(f"{staff_name}'s info successfully updated")
    return redirect("/staff-update")

@app.route("/addStaff")
@login_required
@admin_required
def addstaff():
    staff_name = request.args.get("staffname")
    
    # connect to database
    db, conn = db_connect(DB_PATH)

    # check if client name is already in the database
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    query = db.fetchone()
    conn.close()

    # return result
    if query:
        return jsonify(True)
    else:
        return jsonify(False)

@app.route("/staff/view-staff-info")
@login_required
@admin_required
def view_staff():
    db, conn = db_connect(DB_PATH)

    # Get basic staff info
    db.execute("SELECT name, rbt, tier, color FROM staff ORDER BY name ASC")
    staff_info = [dict(row) for row in db.fetchall()]

    # replace numbers with text
    for row in staff_info:
        if row["color"] == 1:
            row["color"] = "Green"
        elif row["color"] == 2:
            row["color"] = "Yellow"
        else:
            row["color"] = "Red"

        if row["rbt"] == 1:
            row["rbt"] = "Yes"
        else:
            row["rbt"] = "No"

    # get team information
    db.execute("SELECT clients.name, staff.name FROM teams JOIN staff ON staff.staffID=teams.staffID JOIN clients ON clients.clientID=teams.clientID ORDER BY staff.name")

    # convert to dictionary, ordered by staff
    team = []
    team_dict = {}
    for row in db.fetchall():
        item = list(row)
        item[0] = unscramble(item[0])

        if item[1] not in team_dict.keys():  
            team = []

        if item[0] not in team:
            team.append(item[0])
            team_dict[item[1]] = team

    # close database, render staff tables
    conn.close()
    return render_template("view-staff-info.html", staff_info = staff_info, staff_teams = team_dict)

@app.route("/staff/view-staff-hours")
@login_required
@admin_required
def view_staff_hours():
    db, conn = db_connect(DB_PATH)

    # get staff hours
    db.execute("SELECT staff.name, monday, tuesday, wednesday, thursday, friday FROM staffhours JOIN staff ON staffhours.staffID = staff.staffID ORDER BY staff.name")
    staff_hours = db.fetchall()

    # close database, render staff tables         
    conn.close()
    return render_template("view-staff-hours.html", staff_hours = staff_hours)

@app.route("/staff/view-staff-attendance")
@login_required
@admin_required
def view_staff_att():
    db, conn = db_connect(DB_PATH)

    # get staff attendance
    db.execute("SELECT name, mon, tue, wed, thu, fri FROM staff ORDER BY name")
    staff_att = [dict(row) for row in db.fetchall()]

    # replace numbers with text
    for row in staff_att:
        for day in row.keys():
            if day == "name":
                continue
            if row[day] == 1:
                row[day] = "Present"
            else:
                row[day] = "OUT"

    conn.close()
    return render_template("view-staff-att.html", staff_att=staff_att)

@app.route("/classrooms", methods=["GET","POST"])
@login_required
@admin_required
def classrooms():
    # --- GET requests --- #
    if request.method == "GET":
        db, conn = db_connect(DB_PATH)

        # get all staff
        db.execute("SELECT name FROM staff")
        staff_query = db.fetchall()

        # get classrooms
        db.execute("SELECT classroom FROM classrooms")
        class_rms = db.fetchall()

        return render_template("classrooms.html", staff_query = staff_query, class_rms = class_rms)

    # --- POST requests --- #
    # prepare feeback for errors, connet to db
    session["error"] = 1
    db, conn = db_connect(DB_PATH)

    # validate class name forms
    if not request.form.get("class_name"):
        flash("Please provide a classroom name")
        return redirect ("/classrooms")
    classroom = request.form.get("class_name")
    db.execute("SELECT classID FROM classrooms WHERE classroom=?", (classroom,))
    if db.fetchone():
        flash(f"{classroom} is already in the database")
        return redirect ("/classrooms")

    # validate time forms
    if not request.form.get("class_hours_start") or not request.form.get("class_hours_end"):
        flash("Please provide classroom start and end times")
        return redirect("/classrooms")

    # check hour data is in the correct format
    class_hours_start = request.form.get("class_hours_start")
    class_hours_end = request.form.get("class_hours_end")
    time = re.compile(r"[012][0-9]:30")
    if not time.match(class_hours_start) or not time.match(class_hours_end):
        flash("Incorrect time format")
        return redirect("/classrooms")

    class_hours = class_hours_start + "-" + class_hours_end

    # build weekly hours list
    days_toupdate = []
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        if request.form.get(day) != day and request.form.get(day) != None: # change to or?
            flash("Invalid day data")
            return redirect("/classrooms")

        if not request.form.get(day):
            days_toupdate.append(None)
        else:
            days_toupdate.append(class_hours)
    
    # validate teacher forms
    teachers = []
    count = 0
    for teacher in [request.form.get("class_teacher1"), request.form.get("class_teacher2")]:
        if teacher:
            count += 1
        if teacher == None or teacher not in teachers:
            teachers.append(teacher)
        else:
            teachers.append(None)
    if count < 1:
        flash("Please select at least one teacher")
        return redirect("/classrooms")

    # validate substitute forms
    subs= []
    count = 0
    for sub in ["sub1", "sub2", "sub3", "sub4"]:
        if request.form.get(sub):
            count += 1
        if request.form.get(sub) == None or request.form.get(sub) not in subs:
            subs.append(request.form.get(sub))
        else:
            subs.append(None)
    if count < 1:
        flash("Please select at least one substitute teacher")
        return redirect("/classrooms")

    # ensure teacher are not accidentially inserted as subs
    for t in teachers:
        if t == None:
            continue
        for s in subs:
            if s == None:
                continue
            if t == s:
                flash(f"{t} cannot be both a teacher and a sub for {classroom}")
                return redirect("/classrooms")

    # check that all supplied teachers are in database
    teachers = teachers + subs
    teachers_filtered = [teacher for teacher in teachers if teacher]
    for teacher in teachers_filtered:
        db.execute("SELECT name FROM staff WHERE name=?", (teacher,))
        name = db.fetchone()["name"]

        if not name:
            flash(f"{teacher} was not found in the database")
            return redirect("/classrooms")

    # check teacher amount requirement field
    class_rq = request.form.get("class_rq")
    try:
        if int(class_rq) not in {1, 2, 3}:
            flash("Invalid required number of teachers input")
            return redirect("/classrooms")
    except:
            flash("Invalid required number of teachers input")
            return redirect("/classrooms")

    # prepare classroom data
    teachers.insert(0, class_rq)
    teachers.insert(0, classroom)

    # insert classroom data into the databvase
    db.execute("INSERT INTO classrooms (classroom, req, teacher1, teacher2, sub1, sub2, sub3, sub4) VALUES(?,?,?,?,?,?,?,?)", teachers)
    db.execute("SELECT classID FROM classrooms WHERE classroom=?", (classroom,))
    try:
        classID = db.fetchone()["classID"]
    except TypeError:
        flash("No classroom of that name in the database")
        return redirect("/classrooms")

    # get classroom ID, insert classroom hours
    days_toupdate.insert(0, classID)
    db.execute("INSERT INTO classroomhours (classID, monday, tuesday, wednesday, thursday, friday) VALUES(?,?,?,?,?,?)", days_toupdate)
    conn.commit()
    conn.close()
    
    # return success
    session["error"] = 0
    flash(f"{classroom} successfully added")
    return redirect("/classrooms")

@app.route("/classrooms-remove", methods=["POST"])
@login_required
@admin_required
def classrooms_remove():
    # prepare feedback for errors
    session["error"] = 1
    classrm = request.form.get("slct_class")
    if classrm:
        db, conn = db_connect(DB_PATH)
        db.execute("SELECT classID FROM classrooms WHERE classroom=?", (classrm,))
        class_id = db.fetchone()
        if class_id:
            db.execute("DELETE FROM classrooms WHERE classroom=?", (classrm,))
            db.execute("DELETE FROM classroomhours WHERE classID=?", (class_id["classID"],))
            conn.commit()
            conn.close()
            session["error"] = 0
            flash(f"{classrm} successfuly deleted")
            return redirect("/classrooms")
        else:
            conn.close()
            flash(f"{classrm} is not in the database")
            return redirect("/classrooms")
    else:
        flash("Please select a classroom to remove")
        return redirect("/classrooms")

@app.route("/classrooms-update", methods=["GET", "POST"])
@login_required
@admin_required
def class_update_form():
    # --- GET requests --- #
    if request.method == "GET":
        db, conn = db_connect(DB_PATH)

        # get classrooms
        db.execute("SELECT classroom FROM classrooms")
        classrm_data = db.fetchall()

        # get classroom teachers
        db.execute("SELECT teacher1, teacher2, sub1, sub2, sub3, sub4 FROM classrooms")
        teacher_data = db.fetchall()
        teacher_names = [name for row in teacher_data for name in row if name]

        # get all teachers
        db.execute("SELECT name FROM staff")
        staff_data = db.fetchall()
        conn.close()
        return render_template("classrooms-update.html", classrm_data = classrm_data, teacher_names = teacher_names, staff_data = staff_data)

    # --- POST requests --- #
    # prepare feedback for errors, connect to db
    session["error"] = 1
    db, conn  = db_connect(DB_PATH)

    # validate classroom field
    if not request.form.get("slct_class"):
        flash("Please provide a classroom to edit")
        return redirect("/classrooms-update")
    classrm = request.form.get("slct_class")

    # check given classroom is in the database
    db.execute("SELECT classID FROM classrooms WHERE classroom=?", (classrm,))
    class_id = db.fetchone()
    if not class_id:
        flash(f"{classrm} is not in the database")
        return redirect("/classrooms-update")

    # validate time forms
    if request.form.get("class_hours_update_start") and request.form.get("class_hours_update_end"):

        # check hour data is in the correct format
        class_hours_start = request.form.get("class_hours_update_start")
        class_hours_end = request.form.get("class_hours_update_end")
        time = re.compile(r"[012][0-9]:30")
        if not time.match(class_hours_start) or not time.match(class_hours_end):
            flash("Incorrect time format")
            return redirect("/classrooms-update")

        class_hours = class_hours_start + "-" + class_hours_end

        # build weekly hours list
        days_toupdate = []
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            if request.form.get(day) != day and request.form.get(day) != None: # change to or?
                flash("Invalid day data")
                return redirect("/classrooms-update")

            if request.form.get(day):
                days_toupdate.append(day)

        # update class_hours
        for item in days_toupdate:
            db.execute(f"UPDATE classroomhours SET {item}=? WHERE classID=?", (class_hours, class_id["classID"]))

    # remove provided staff name NOTE: this assumes that subs and teachers are never the same
    staff_toremove = request.form.get("slct_classTeacher")
    if staff_toremove:
        counter = 0
        for staff in ["teacher1", "teacher2", "sub1", "sub2", "sub3", "sub4"]:
            db.execute(f"SELECT {staff} FROM classrooms WHERE classroom=?", (classrm,))
            teacher = db.fetchone()
            if teacher[staff] and staff_toremove == teacher[staff]:
                db.execute(f"UPDATE classrooms SET {staff}=? WHERE classroom=?", (None, classrm))
                counter += 1
                conn.commit()

        if counter == 0:
            flash(f"Removal not possible, {staff_toremove} is not part of {classrm}")
            return redirect("/classrooms-update")
    
    # add user selected staff to classroom
    if request.form.get("slct_add_sub"):
        staff_toadd = request.form.get("slct_add_sub")

        # check if staff is in staff database
        db.execute("SELECT name FROM staff WHERE name=?", (staff_toadd,))
        if not db.fetchone():
            flash(f"{staff_toadd} is not in the database")
            return redirect("/classrooms-update")
        
        # adding staff member as a teacher
        if request.form.get("add_as") == "t":

            # check staff is not alread part of classroom
            db.execute("SELECT sub1, sub2, sub3, sub4 FROM classrooms WHERE classroom=?", (classrm,))
            subs = db.fetchone()
            for sub in subs:
                if sub == staff_toadd:
                    flash(f"{staff_toadd} is already a part of {classrm}")
                    return redirect("/classrooms-update")
                    
            # look for blank spot to insert new staff
            counter = 0
            for teacher in ["teacher1", "teacher2"]:
                db.execute(f"SELECT {teacher} FROM classrooms WHERE classroom=?", (classrm,))
                spot = db.fetchone()
                if spot[teacher] == staff_toadd:
                    flash(f"{staff_toadd} is already a part of {classrm}")
                    return redirect("/classrooms-update")
                if not spot[teacher]:
                    db.execute(f"UPDATE classrooms SET {teacher}=? WHERE classroom=?", (staff_toadd, classrm))
                    conn.commit()
                    counter +=1
                    break
            if counter == 0:
                flash("No room in class to add new teacher")
                return redirect("/classrooms-update")

        # adding staff member as a sub
        elif request.form.get("add_as") == "s":

            # check staff is not alread part of classroom
            db.execute("SELECT teacher1, teacher2 FROM classrooms WHERE classroom=?", (classrm,))
            teachers = db.fetchone()
            for teacher in teachers:
                if teacher == staff_toadd:
                    flash(f"{staff_toadd} is already a part of {classrm}")
                    return redirect("/classrooms-update")

            # look for blank spot to insert new staff
            counter = 0
            for sub in ["sub1", "sub2", "sub3", "sub4"]:
                db.execute(f"SELECT {sub} FROM classrooms WHERE classroom=?", (classrm,))
                spot = db.fetchone()
                if spot[sub] == staff_toadd:
                    flash(f"{staff_toadd} is already a part of {classrm}")
                    return redirect("/classrooms-update")
                if not spot[sub]:
                    db.execute(f"UPDATE classrooms SET {sub}=? WHERE classroom=?", (staff_toadd, classrm))
                    conn.commit()
                    counter += 1
                    break
            if counter == 0:
                flash("No room in class to add new substitute")
                return redirect("/classrooms-update")
                
        else:
            flash("Invalid radio button data recieved")
            return redirect("/classrooms-update")

    # check for required number of staff data
    if request.form.get("update_rq"):
        try:
            rq = int(request.form.get("update_rq"))
        except ValueError:
            flash("Invalid required number of teachers data received")
            return redirect("/classrooms-update")

        if rq in [1, 2, 3]:
            db.execute("UPDATE classrooms SET req=? WHERE classroom=?", (rq, classrm))
            conn.commit()
        else:
            flash("Invalid required number of teachers data received")
            return redirect("/classrooms-update")

    conn.commit()
    conn.close()
    session["error"] = 0
    flash(f"{classrm} successfully updated")
    return redirect("/classrooms-update")

@app.route("/classrooms-viewinfo")
@login_required
@admin_required
def view_class():
    db, conn = db_connect(DB_PATH)
    db.execute("SELECT classroom, req, teacher1, teacher2, sub1, sub2, sub3, sub4 FROM classrooms")
    class_data = db.fetchall()
    conn.close()
    return render_template("classrooms-view-info.html", class_data = class_data)

@app.route("/classrooms-viewhours")
@login_required
@admin_required
def view_class_hours():
    db, conn = db_connect(DB_PATH)
    db.execute("SELECT classrooms.classroom, monday, tuesday, wednesday, thursday, friday FROM classroomhours INNER JOIN classrooms ON classrooms.classID=classroomhours.classID")
    class_hours = db.fetchall()
    conn.close()
    return render_template("classrooms-view-hours.html", class_hours = class_hours)

@app.route("/schedule", methods=["GET", "POST"])
@login_required
@admin_required
def schedule():
    # when user navigatest to schedule route
    if request.method == "GET":
        return render_template("schedule.html")

    # for POST requests
    # prepare feedback for errors
    session["error"] = 1

    # check that a day is selected
    if request.form.get("schedule_day") not in {"monday", "tuesday", "wednesday", "thursday", "friday"}:
        flash("Please choose a valid day to generate the schedule for")
        return redirect("/schedule")
    
    current_day = request.form.get("schedule_day")
    curr_att_day = shorten_day(current_day)

    # when user generates a schedule
    db, conn = db_connect(DB_PATH)

    # update total hours for all clients
    db.execute(f"SELECT {current_day}, clientID from clienthours")
    staff_hours = db.fetchall()
    for hours in staff_hours:
        if hours[current_day] is None:
            total_hours = 0
        else:
            total_hours = len(create_schhours(hours[current_day]))
        db.execute("UPDATE clients SET totalhours=? WHERE clientID=?", (total_hours, hours["clientID"]))
    conn.commit()
    
    # build staff schedules with nested dicts
    db.execute(f"SELECT name, staffhours.{current_day} FROM staff INNER JOIN staffhours ON staff.staffID = staffhours.staffID WHERE {curr_att_day}=1")
    staff_data = db.fetchall()

    all_staff_sch = {}
    for row in staff_data:
        # NOTE: dynamically generate these times?
        all_staff_sch[row["name"]] = {830: "" , 930: "" , 1030: "" , 1130: "" , 1230: "" , 130: "" , 230: "" , 330: "" , 430: ""}
        for time in all_staff_sch[row["name"]].keys():
            hours = create_schhours(row[current_day])
            if time not in hours:
                all_staff_sch[row["name"]][time] = "OUT"

    # ------------------------------------------------------------------------------------------------------------ #
    # build classroom dicts
    db.execute("SELECT * FROM classrooms")
    class_info = db.fetchall()
    if not class_info:
        flash("No classrooms in database")
        return redirect("/schedule")

    # loop through classrooms
    for i in range(len(class_info)):
        db.execute(f"SELECT {current_day} FROM classroomhours WHERE classID=?", (class_info[i]["classID"],))
        hours_data = db.fetchone()

        if not hours_data:
            flash(f"{class_info[i]['classroom']} has no hours on {current_day} and was not scheduled")
            continue

        class_hours = create_schhours(hours_data[current_day])

        class_sch = {} # may need to empty this differenty
        for hour in class_hours:
            class_sch[hour] = 0

        allclass_teachers = [class_info[i]["teacher1"], class_info[i]["teacher2"], class_info[i]["sub1"], 
                             class_info[i]["sub2"], class_info[i]["sub3"], class_info[i]["sub4"]]
        allclass_teachers = [teacher for teacher in allclass_teachers if teacher]

        class_teachers = []
        # create teacher list, removing those that are absent from work
        for teacher in allclass_teachers:
            db.execute(f"SELECT {curr_att_day} FROM staff WHERE name=?", (teacher,))
            if db.fetchone()[curr_att_day] == 1:
                class_teachers.append(teacher)

        # if sublist is empty prompt user to add teacher to sublist
        if len(class_teachers) < class_info[i]["req"]:
            flash(f'{class_info[i]["classroom"]} sublist is empty or too small. Please add staff to the sublist to continue')
            return redirect("/schedule")

        # add classroom to teacher's schedule
        full_hours = []
        for teacher in class_teachers:
            # get staff id
            db.execute("SELECT staffID FROM staff WHERE name=?", (teacher,))
            teacher_id = db.fetchone()["staffID"]

            # get teacher hours
            db.execute(f"SELECT {current_day} FROM staffhours where staffID=?", (teacher_id,))
            teacher_hours = db.fetchone()[current_day]
            teacher_hours = create_schhours(teacher_hours)

            # remove hours that are not class times, that are "full"
            teacher_hours = [hour for hour in teacher_hours if hour in class_sch.keys()]
            teacher_hours = [hour for hour in teacher_hours if hour not in full_hours]

            # end loop if no hours left to schedule
            if not teacher_hours:
                break

            # schedule required number of staff
            for hr in teacher_hours:
                if all_staff_sch[teacher][hr] != "":
                    print("overlap error!!!!")

                all_staff_sch[teacher][hr] = class_info[i]["classroom"]
                class_sch[hr] += 1

            # track hours that no longer need teachers
            full_hours = [item[0] for item in class_sch.items() if item[1] == class_info[i]["req"]]
    # ------------------------------------------------------------------------------------------------------------ #

    # get client data (where client/staff are present, ordered by color and total hours)
    db.execute(f"SELECT * FROM clients WHERE {curr_att_day}=1 ORDER BY color DESC, totalhours DESC") 
    client_data = db.fetchall()

    # create schedule dicts for each client
    # NOTE: dynamically generate these times?
    c_dict = {830: "---" , 930: "---" , 1030: "---" , 1130: "---" , 1230: "---" , 130: "---" , 230: "---" , 330: "---" , 430: "---"} 
    clients = [c_dict.copy() for row in client_data]

    # update each client's schedule
    client_num = 0
    for client in clients:

        # prepare client specific info/variables
        client_ID = client_data[client_num]["clientID"]
        client_name = unscramble(client_data[client_num]["name"])
        db.execute(f"SELECT {current_day} FROM clienthours WHERE clientID=?", (client_ID,))
        # NOTE: check for None here?
        client_hours = db.fetchone()[current_day]
        
        # generate a list of the client's scheduable hours
        times = create_schhours(client_hours)
        # update client's scheduling dictionary
        for time in times:
            if time in client.keys():
                client[time] = 0

        # get availible staff members are on the client's team
        db.execute(f"SELECT clientID, staff.name FROM teams INNER JOIN staff ON staff.staffID = teams.staffID WHERE clientID = ? AND {curr_att_day}=1", (client_ID,))
        team_members = db.fetchall()
        client_team = [staff["name"] for staff in team_members]
        client["Name"] = client_name

        # schedule two hours
        client_sch = client

        # generate current client's schedule
        client_sch = generate_schedules(client_ID, client_name, client_team, client_sch, all_staff_sch, curr_att_day)
        
        # write client's schedule to csv
        header = ("Name", "Time", "Staff")
        try:
            with open(os.path.join(app.instance_path, "client_schedule_" + curr_att_day + ".csv"), "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                if client_num == 0:
                    writer.writerow((current_day.capitalize(),))
                    writer.writerow(header)

                client_items = list(client_sch.items())
                client_name = client_items.pop()[1]
                first_row = (client_name, client_items[0][0], client_items.pop(0)[1])
                writer.writerow(first_row)
                for items in client_items:
                    row = ("", items[0], items[1])
                    writer.writerow(row)
                writer.writerow("")

        except PermissionError:
            flash("Could not write schedule to file, permission was denied")
            return redirect("/schedule")

        # increment through clients
        client_num += 1

    # short staff in schedule into alphabetical list
    sorted_staff = sorted(all_staff_sch)

    # write staff's schedule to csv
    try:
        with open(os.path.join(app.instance_path, "staff_schedule_" + curr_att_day + ".csv"), "a", newline="") as csvfile2:
            writer = csv.writer(csvfile2)
            header = ("Name", "Time", "Client")
            writer.writerow((current_day.capitalize(),))
            writer.writerow(header)

            for staff_name in sorted_staff:
                counter = 0
                for item in all_staff_sch[staff_name].items():
                    if counter == 0:
                        row = (staff_name, item[0], item[1])
                    else:
                        row = ("", item[0], item[1])
                    writer.writerow(row)
                    counter += 1
                writer.writerow("")

    except PermissionError:
        flash("Could not write schedule to file, permission was denied")
        return redirect("/schedule")

    conn.close()

    # encrypt files, removed unencrypted files
    files = {"staff_schedule_" + curr_att_day + ".csv", "client_schedule_" + curr_att_day + ".csv"}
    buffer = 64 * 1024
    key = "abcofnc1!"
    
    for f in files:
       pyAesCrypt.encryptFile(os.path.join(app.instance_path, f), os.path.join(app.instance_path, (f + ".aes")), key, buffer)
       os.remove(os.path.join(app.instance_path, f))

    # redirect to downloads page, prepare feedback for info
    session["error"] = 0
    flash("Success")
    return redirect("/schedule")

@app.route("/view-schedule/<string:catagory>", methods=["GET", "POST"])
@login_required
def view_schedule(catagory):
    # --- GET REQUESTS --- #
    if request.method == "GET":
        current_day = ["Pick a day"]
        if catagory == "both":
            schedules = []
            return render_template("view-schedule.html", schedules = schedules, current_day = current_day)
        elif catagory == "staff":
            staff_schedule = []
            return render_template("staff-or-client-schedule.html", catagory = catagory, staff_schedule = staff_schedule, current_day = current_day)
        elif catagory == "clients":
            client_schedule = []
            return render_template("staff-or-client-schedule.html", catagory = catagory, client_schedule = client_schedule, current_day = current_day)
        else:
            flash("URL invalid")
            return redirect("/")

    # --- POST REQUESTS --- #
    # prepare feedback varibles
    session["error"] = 1
    error_path = "/view-schedule/" + catagory

    # get correct form data
    if catagory == "both":
        day = request.form.get("view_schedule_day_both")
    else:
        day = request.form.get("view_schedule_day")
    
    if not day:
        flash("Please select a day")
        return redirect(error_path)

    if day not in {"mon", "tue", "wed", "thu", "fri"}:
        flash("Invalid data submitted")
        return redirect(error_path)

    # prepare variables
    buffer = 64 * 1024
    key = "abcofnc1!"
    files = ("client_schedule_" + day + ".csv", "staff_schedule_" + day + ".csv")
    schedules = []

    # decrypt each schedule file, read each file into a list, remove the decrypted file
    for f in files:
        encrypted_path = os.path.join(app.instance_path, (f + ".aes"))
        path = os.path.join(app.instance_path, f)

        try:
            pyAesCrypt.decryptFile(encrypted_path, path, key, buffer)
        except:
            flash("No file found")
            return redirect(error_path)
        try:
            with open(path, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                current_day = next(reader)
                next(reader)
                schedule = [row for row in reader]
                schedules.append(schedule)
        except csv.Error as e:
            flash(f"Error: {e}")
            return redirect(error_path)

        os.remove(path)

    # render schedules tables
    if catagory == "both":
        return render_template("view-schedule.html", schedules = schedules, current_day = current_day)
    elif catagory == "clients":
        return render_template("staff-or-client-schedule.html", catagory = catagory, client_schedule = schedules[0], current_day = current_day)
    elif catagory == "staff":
        return render_template("staff-or-client-schedule.html", catagory = catagory, staff_schedule = schedules[1], current_day = current_day)
    else:
        flash("URL invalid")
        return redirect("/")
    
@app.route("/download", methods=["GET", "POST"])
@login_required
@admin_required
def downloadpage():
    # --- GET REQUESTS --- #
    if request.method == "GET":
        return render_template("schedule.html")

    # --- POST REQUESTS --- #
    # prepare server feedback as errors
    session["error"] = 1
    day = request.form.get("download_day")
    schedule = request.form.get("schedule_type")

    # validate day select values
    if day not in {"mon", "tue", "wed", "thu", "fri"}:
        flash("You must select a day")
        return redirect("/schedule")

    # validate radio values
    if schedule not in {"s", "c"}:
        flash("You must choose staff or client schedule")
        return redirect("/schedule")
    
    # add CSV file type ending
    day += ".csv"

    # create file name to be dowloaded
    if schedule == "s":
        filename = "staff_schedule_" + day
    else:
        filename = "client_schedule_" + day

    buffer = 64 * 1024
    key = "abcofnc1!"

    # prepare file names, decrypt file
    encrypted_path = os.path.join(app.instance_path, (filename + ".aes"))
    path = os.path.join(app.instance_path, filename)
    try:
        pyAesCrypt.decryptFile(encrypted_path, path, key, buffer)
    except:
        flash("No file found")
        return redirect("/schedule")

    # server file from memory, overwrite file, then delete file
    # code from: https://stackoverflow.com/questions/40853201/remove-file-after-flask-serves-it?rq=1, by davidism
    def generate():
        with open(path) as f:
            yield from f
        
        # subprocess.check_call(f"srm {path}")
        with open(path, "w", newline = "") as csvfile:
            writer = csv.writer(csvfile)
            for i in range(10000):
                writer.writerow(["abcdefghijklmnopwrstuvwxyz", "abcdefghijklmnopwrstuvwxyz", "abcdefghijklmnopwrstuvwxyz", "abcdefghijklmnopwrstuvwxyz", "abcdefghijklmnopwrstuvwxyz"])

        os.remove(path)
    
    r = app.response_class(generate(), mimetype="text/csv")
    r.headers.set("Content-Disposition", "attachment", filename=filename)
    return r

@app.route("/database", methods=["GET"])
@login_required
@admin_required
def manage_database():
    session["error"] = 1
    mode = request.args.get("manage_db")

    # validate form
    if not mode or mode not in {"r", "b"}:
        flash("Please select an action to preform on the database")
        return redirect("/schedule")

    # backup or restore
    session["error"] = 0
    if mode == "b":
        db_backup(DB_PATH)
        flash("Backup Complete")
    if mode == "r":
        db_restore(DB_PATH)
        flash("Data Base Restored")

    return redirect("/schedule")

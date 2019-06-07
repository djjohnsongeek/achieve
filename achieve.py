import os
import sqlite3
import re
import csv
import pyAesCrypt
# import subprocess

from flask import Flask
from flask import render_template, request, session, redirect, Response, jsonify, json, send_from_directory, flash
from sqlite3 import Error
from random import randrange
from werkzeug.security import check_password_hash, generate_password_hash
from jinja2 import Environment, FileSystemLoader

from SQL import db_connect
from server import generate_schedules, convert_strtime, create_schhours, login_required, shorten_day, lengthen_day, admin_required
from cypher import scramble, unscramble

# NOTE: need to replace annoying single error page with client side UI feedback
# NOTE: need to send POST requests with AJAX
# NOTE: need to review code, optimize and improve design and style, use custom fuctions as well as revamp comments

"""
Achieve allows users to add, edit and remove staff and client information to and from database.
From the '/schedule' route it generates a daily schedule and saves it as an csv file which can be downloaded.
(The 'generate schedule' is still in progress, and 'download csv file' is yet to be implemented)
"""
DB_URL = "C:\\Users\\Johnson\\Documents\\Projects\\achieve\\achieve.db"

# initialize app
app = Flask(__name__, instance_path="C:\\Users\\Johnson\\Documents\\Projects\\Achieve\\protected")
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
        db, conn = db_connect(DB_URL)
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
    db, conn = db_connect(DB_URL)

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
        db, conn = db_connect(DB_URL)
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
    start = convert_strtime(client_hours_start)
    end = convert_strtime(client_hours_end)
  
    # generate a list of the staff's scheduable hours
    total_hours = len(create_schhours(start, end))

    # combine start and end times into one variable
    client_hours = client_hours_start + "-" + client_hours_end

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
    if len(t_members) == 0:
        flash(f"Please provide {unscramble(client_name)} with at least one Team Member")
        return redirect("/clients")

    # remove duplicates
    unique_members = set(t_members)
    
    # connect to database
    db, conn = db_connect(DB_URL)

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

@app.route("/clients-update")
@login_required
@admin_required
def clients_update_form():
    db, conn = db_connect(DB_URL)
    db.execute("SELECT name FROM staff")
    staff_query = db.fetchall()
    db.execute("SELECT name FROM clients")
    client_query = db.fetchall()
    conn.close()
    return render_template("clients-update.html", staff_query=staff_query, client_query=client_query, unscramble=unscramble)

@app.route("/addclient", methods=["GET"])
def addclient():
    clientname = scramble(request.args.get("clientname"))
    
    # connect to database
    db, conn = db_connect(DB_URL)

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
    db, conn = db_connect(DB_URL)

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
    db, conn = db_connect(DB_URL)

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
    db, conn = db_connect(DB_URL)

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

@app.route("/clients/remove", methods=["POST"])
def remove_client():\
    # setup feedback as error
    session["error"] = 1

    # validate remove_client form
    if not request.form.get("slct_client"):
        flash("Please provide the client name to be removed")
        return redirect("/clients")

    client_name = request.form.get("slct_client")

    # connect to database
    db, conn = db_connect(DB_URL)

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

@app.route("/clients/update", methods=["POST"])
def update_client():
    # setup feedback for errors
    session["error"] = 1

    # ensure client name is filled out
    if not request.form.get("update_client"):
        flash("Please provide a client's name")
        return redirect("/clients")

    client_name = request.form.get("update_client")

    # connect to db
    db, conn = db_connect(DB_URL)

    # check if client is in the data base
    db.execute("SELECT clientID FROM clients WHERE name=?", (client_name,))
    client_info = db.fetchone()
    if not client_info:
        flash(f"{unscramble(client_name)} was not found in the database")
        return redirect("/clients")

    # get and insert new hours data
    if request.form.get("new_client_hours_start") and request.form.get("new_client_hours_end"):

        client_hours_start = request.form.get("new_client_hours_start")
        client_hours_end = request.form.get("new_client_hours_end")

        # ensure proper data format
        time = re.compile(r"[012][0-9]:30")
        if not time.match(client_hours_end) or not time.match(client_hours_start):
            flash("Invalid time format")
            return redirect("/clients")

        # get client's total number of hours
        total_hours = len(create_schhours(convert_strtime(client_hours_start), convert_strtime(client_hours_end)))
        client_hours = client_hours_start + "-" + client_hours_end

        # store client hours
        client_days = []
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            # validate day data
            if request.form.get(day) != day and request.form.get(day) != None:
                flash("Invalid day data")
                return redirect("/clients")

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
                return redirect("/clients")
        except ValueError:
            flash("Invalid attendance data")
            return redirect("/clients")

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
            return redirect("/clients")

        # update the data
        item[0] = shorten_day(item[0])
        db.execute(f"UPDATE clients SET {item[0]}=? WHERE clientID=?", (item[1], client_info["clientID"]))

    # change client's color classification if needed
    if request.form.get("update_color"):
        try:
            update_color = int(request.form.get("update_color"))
        except ValueError:
            flash("Invalid client classification data")
            return redirect("/clients")

        if update_color not in {1, 2, 3}:
            flash("Invalid client classification data")
            return redirect("/clients")
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
            return redirect("/clients")
        
        # check if teacher is already on client's team
        db.execute("SELECT * FROM teams WHERE clientID=? AND staffID=?", (client_info["clientID"], staff_info["staffID"]))
        team_info = db.fetchone()
        
        # check if data recieved matches expected pattern
        regex = re.compile(r"add|remove")
        result = regex.match(add_or_remove)

        if not result:
            flash("Invalid Add or Remove data")
            return redirect("/clients")

        if add_or_remove == "add":
            if team_info:
                flash(f"{new_teacher} is already on {unscramble(client_name)}'s team")
                return redirect("/clients")
            else:
                # add selected teacher to selected Client's team
                db.execute("INSERT INTO teams (clientID, staffID) VALUES(?,?)", (client_info["clientID"], staff_info["staffID"]))

        if add_or_remove == "remove":
            if not team_info:
                flash(f"No removal necessary: {new_teacher} and {unscramble(client_name)} are not on the same team")
                return redirect("/clients")
            else:
                # remove selected teacher from selected Client's team
                db.execute("DELETE FROM teams WHERE clientID=? and staffID=?", (client_info["clientID"], staff_info["staffID"]))

    # commit changes, change feedback to info
    conn.commit()
    conn.close()

    session["error"] = 0
    flash(f"{unscramble(client_name)}'s info has been updated")
    return redirect("/clients")

@app.route("/staff", methods=["POST", "GET"])
@login_required
@admin_required
def staff():
    if request.method == "GET":
        # connect to database
        db, conn = db_connect(DB_URL)

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
    db, conn = db_connect(DB_URL)

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

@app.route("/staff-update")
@login_required
@admin_required
def staff_update_form():
    # connect to database
    db, conn = db_connect(DB_URL)

    # retrieve all staff names
    db.execute("SELECT name FROM staff")
    staff_names = db.fetchall()

    # close connection to database
    conn.close()
    return render_template("staff-update.html", staff_names=staff_names)

@app.route("/staff/view-staff-info")
@login_required
@admin_required
def view_staff():
    db, conn = db_connect(DB_URL)

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
    db, conn = db_connect(DB_URL)

    # get staff hours
    db.execute("SELECT staff.name, monday, tuesday, wednesday, thursday, friday FROM staffhours JOIN staff ON staffhours.staffID = staff.staffID ORDER BY staff.name")
    staff_hours = db.fetchall()

    # close database, render staff tables         
    conn.close()
    return render_template("view-staff-hours.html", staff_hours = staff_hours)

@app.route("/staff/view-staff-attendance")
@login_required
@admin_required
def vew_staff_att():
    db, conn = db_connect(DB_URL)

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
    db, conn = db_connect(DB_URL)

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

    # commit changes and close database
    conn.commit()
    conn.close()
    
    # change feedback to info
    session["error"] = 0
    flash(f"{staff_name} has been deleted")
    return redirect("/staff")

@app.route("/staff/update", methods=["POST"])
def staff_update():
    # prepare feedback for errors
    session["error"] = 1

    # check that staff name is filled out
    if not request.form.get("slct_staff_update"):
        flash("Please provide a staff member's name")
        return redirect("/staff")

    staff_name = request.form.get("slct_staff_update")
    
    # connect to db
    db, conn = db_connect(DB_URL)

    # check if staff name is in database
    db.execute("SELECT staffID FROM staff WHERE name=?", (staff_name,))
    staff_info = db.fetchone()
    if not staff_info:
        flash(f"{staff_name} is not in the database")
        return redirect("/staff")

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
            return redirect("/staff")

    # if Tier radio is chosen
    if request.form.get("tier_update"):
        try:
            tier = int(request.form.get("tier_update"))
        except ValueError:
            flash("Teacher tier field must be a digit")
            return redirect("/staff")
        
        if tier in {1,2,3}:
            db.execute("UPDATE staff SET tier=?, color=? WHERE staffID=?", (tier, tier, staff_info["staffID"]))
        else:
            flash("Invalid teacher tier data")
            return redirect("/staff")

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
                    return redirect("/staff")

                if request.form.get(day) == day:
                    staff_days.append(day)

            for items in staff_days:
                db.execute(f"UPDATE staffhours SET {items}=? WHERE staffID=?", (staff_hours, staff_info["staffID"]))

        else:
            flash("Invalid time format")
            return redirect("/staff")

    # staff color category
    if request.form.get("staff_color"):
        try:
            color = int(request.form.get("staff_color"))
        except ValueError:
            flash("Invalid staff classification value")
            return redirect("/staff")

        if color not in {1,2,3}:
            flash("Invalid staff classification value")
            return redirect("/staff")
        else:
            db.execute("UPDATE staff SET color=? WHERE staffID=?", (color, staff_info["staffID"]))

    # prepare staff attendance variables
    staff_att = []
    for day in ["mon", "tue", "wed", "thu", "fri"]:
        try:
            if request.form.get(day) != None and int(request.form.get(day)) not in {0,1}:
                flash("Invalid attendance data")
                return redirect("/staff")

        except ValueError:
            flash("Invalid attendance data")
            return redirect("/staff")

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
            return redirect("/staff")

        item[0] = shorten_day(item[0])
        db.execute(f"UPDATE staff SET {item[0]}=? WHERE staffID=?", (item[1], staff_info["staffID"]))

    # close database and save changes
    conn.commit()
    conn.close()

    # prepare feedback info
    session["error"] = 0
    flash(f"{staff_name}'s info successfully updated")
    return redirect("/staff-update")

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
    db, conn = db_connect(DB_URL)

    # update total hours for all clients
    db.execute(f"SELECT {current_day}, clientID from clienthours")
    staff_hours = db.fetchall()
    for hours in staff_hours:
        if hours[current_day] is None:
            total_hours = 0
        else:
            times = hours[current_day].split('-')
            total_hours = len(create_schhours(convert_strtime(times[0]), convert_strtime(times[1])))

        db.execute("UPDATE clients SET totalhours=? WHERE clientID=?", (total_hours, hours["clientID"]))
    conn.commit()
    
    # build staff schedules with nested dicts
    db.execute(f"SELECT name FROM staff where {curr_att_day}=1")
    staff_data = db.fetchall()

    all_staff_sch = {}
    for staff in staff_data:
        all_staff_sch[staff["name"]] = {830: "" , 930: "" , 1030: "" , 1130: "" , 1230: "" , 130: "" , 230: "" , 330: "" , 430: ""} # NOTE: dynamically generate these times?

    # get client data (where client/staff are present, ordered color and total hours)
    # sort selection by color (highest first) then by number of hours (highest first)
    db.execute(f"SELECT * FROM clients WHERE {curr_att_day}=1 ORDER BY color DESC, totalhours DESC") 
    client_data = db.fetchall()

    # create schedule dicts for each client
    c_dict = {830: "---" , 930: "---" , 1030: "---" , 1130: "---" , 1230: "---" , 130: "---" , 230: "---" , 330: "---" , 430: "---"} # NOTE: dynamically generate these times?
    clients = [c_dict.copy() for row in client_data]

    # update each client's schedule
    client_num = 0
    for client in clients:

        # prepare client specific info/variables
        client_ID = client_data[client_num]["clientID"]
        client_name = unscramble(client_data[client_num]["name"])
        db.execute(f"SELECT {current_day} FROM clienthours WHERE clientID=?", (client_ID,))
        client_hours = db.fetchone()[current_day].split("-")
        
        # generate a list of the client's scheduable hours
        times = create_schhours(convert_strtime(client_hours[0]), convert_strtime(client_hours[1]))

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
            with open(os.path.join(app.instance_path, "client_schedule.csv"), "a", newline="") as csvfile:
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

   # write staff's schedule to csv NOTE: need to output in alphabetical order
    try:
        with open(os.path.join(app.instance_path, "staff_schedule.csv"), "a", newline="") as csvfile2:
            writer = csv.writer(csvfile2)
            header = ("Name", "Time", "Client")
            writer.writerow((current_day.capitalize(),))
            writer.writerow(header)

            for staff in all_staff_sch.items():
                first_row = (staff[0], 830, staff[1][830])
                writer.writerow(first_row)
                counter = 0
                for key in staff[1].keys():
                    if counter == 0:
                        counter += 1
                        continue
                    row = ("", key, staff[1][key])
                    writer.writerow(row)
                writer.writerow("")

    except PermissionError:
        flash("Could not write schedule to file, permission was denied")
        return redirect("/schedule")

    conn.close()

    # encrypt files, removed unencrypted files
    files = {"staff_schedule.csv", "client_schedule.csv"}
    buffer = 64 * 1024
    key = "abcofnc1!"
    
    for f in files:
       pyAesCrypt.encryptFile(os.path.join(app.instance_path, f), os.path.join(app.instance_path, (f + ".aes")), key, buffer)
       os.remove(os.path.join(app.instance_path, f))

    # redirect to downloads page, prepare feedback for info
    session["error"] = 0
    flash("Success")
    return redirect("/download")

@app.route("/view-schedule/<string:catagory>")
@login_required
def view_schedule(catagory):

    # prepare variables
    buffer = 64 * 1024
    key = "abcofnc1!"
    files = ("client_schedule.csv", "staff_schedule.csv")
    schedules = []

    # decrypt each schedule file, read each file into a list, remove the decrypted file
    for f in files:
        encrypted_path = os.path.join(app.instance_path, (f + ".aes"))
        path = os.path.join(app.instance_path, f)

        try:
            pyAesCrypt.decryptFile(encrypted_path, path, key, buffer)
        except:
            session["error"] = 1
            flash("No file found")
            return redirect("/schedule")
        try:
            with open(path, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                current_day = next(reader)
                next(reader)
                schedule = [row for row in reader]
                schedules.append(schedule)
        except csv.Error as e:
            session["error"] = 1
            flash(f"Error: {e}")
            return redirect("/schedule")

        os.remove(path)

    # render schedules tables
    if catagory == "both":
        return render_template("view-schedule.html", schedules = schedules, current_day = current_day)
    elif catagory == "clients":
        return render_template("staff-or-client-schedule.html", client_schedule = schedules[0], current_day = current_day)
    elif catagory == "staff":
        return render_template("staff-or-client-schedule.html", staff_schedule = schedules[1], current_day = current_day)
    else:
        session["error"] = 1
        flash("URL invalid")
        return redirect("/")
    
@app.route("/download")
@login_required
@admin_required
def downloadpage():
    return render_template("downloads.html")

@app.route("/download/<path:filename>")
@login_required
def download(filename):
    buffer = 64 * 1024
    key = "abcofnc1!"

    # prepare file names, decrypt file
    encrypted_path = os.path.join(app.instance_path, (filename + ".aes"))
    path = os.path.join(app.instance_path, filename)
    try:
        pyAesCrypt.decryptFile(encrypted_path, path, key, buffer)
    except:
        session["error"] = 1
        flash("No file found")
        return redirect("/download")

    # server file from memory, delete file
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
from turtle import update
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from datetime import datetime

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure Library to use SQLite database
db = SQL("sqlite:///ticket.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # insert dataes to property table
    db.execute("INSERT INTO property (cash, id) VALUES (?, ?)", 0, session["user_id"])

    # render homepage
    return render_template("index.html")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        
        username = request.form.get("username")
        password = request.form.get("password")
        if not password or not username:
            return apology("Please enter all fidds")

        db.execute("UPDATE users SET password = ?, username = ? WHERE id = ?", password, username, session["user_id"])

        return redirect("/")

    else:
        return render_template("change.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    # dict charge of vehicles
    charge = dict()
    charge["Airplane"] = 50
    charge["Train"] = 35
    charge["Bus"] = 30

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # get origin & destination & vehicale from page
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        vehicle = request.form.get("vehicle")

        # check to enter origin & destination & vehicale
        if not origin or not destination:
            return apology("Please enter all filds")
        if vehicle == None:
            return apology("Please enter vehicle")

        # check to have such money
        if float(db.execute("SELECT cash FROM property WHERE id = ?", session["user_id"])[0]["cash"]) < charge[vehicle]:
            return apology("Sorry we do not have such money")
        
        # get date & time
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day
        hour = datetime.now().hour
        minute = datetime.now().minute

        # insert data to buy table
        db.execute("INSERT INTO buy (id, year, month, day, hour, minute, vehicle, origin, destination, exist) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], year, month, day, hour, minute, vehicle, origin, destination, 1)
        money = float(db.execute("SELECT cash FROM property WHERE id = ?", session["user_id"])[0]["cash"])
        db.execute("UPDATE property SET cash = ? WHERE id = ?", money - charge[vehicle], session["user_id"])

        # redirect to index
        return redirect("/")

    else:

        # rendering buy page
        return render_template("buy.html")

@app.route("/refund", methods=["GET", "POST"])
@login_required
def refund():

    # dict charge of vehicles
    charge = dict()
    charge["Airplane"] = 50
    charge["Train"] = 35
    charge["Bus"] = 30

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get origin & destination & vehicale from page
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        vehicle = request.form.get("vehicle")

        # check to enter origin & destination & vehicale
        if not origin or not destination:
            return apology("Please enter all filds")
        if vehicle == None:
            return apology("Please enter vehicle")

        # check to ticket exist
        if not db.execute("SELECT exist FROM buy WHERE id = ? and origin = ? and destination = ? and vehicle = ?", session["user_id"], origin, destination, vehicle)[0]["exist"]:
            return apology("Sorry you dont have this ticket")

        # get date & time
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day
        hour = datetime.now().hour
        minute = datetime.now().minute

        # insert data to refund & buy table
        db.execute("INSERT INTO refund (id, year, month, day, hour, minute, vehicle, origin, destination) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], year, month, day, hour, minute, vehicle, origin, destination)
        db.execute("UPDATE buy SET exist = ? WHERE id = ? and origin = ? and destination = ? and vehicle = ?", 0, session["user_id"], origin, destination, vehicle)
        money = float(db.execute("SELECT cash FROM property WHERE id = ?", session["user_id"])[0]["cash"])
        db.execute("UPDATE property SET cash = ? WHERE id = ?", money + charge[vehicle], session["user_id"])

        # redirect to index
        return redirect("/")

    else:

        # get data from buy table
        trip = db.execute("SELECT origin, destination, vehicle FROM buy WHERE id = ? and exist = ?", session["user_id"], 1)

        # rendering refund page
        return render_template("refund.html", trip=trip)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get name & number & cash from page
        name = request.form.get("name")
        number = request.form.get("number")
        cash = request.form.get("cash")

        # check to enter name & number & cash
        if not number or not name or not cash:
            return apology("Please enter all filds")
        try:
            cash = float(cash)
        except:
            return apology("please enter number to cash")

        # update property table
        db.execute("UPDATE property SET name = ?, number = ?, cash = ? WHERE id = ?", name, number, cash, session["user_id"])

        # redirect to index
        return redirect("/")

    else:

        # get datas from buy & property tale    
        property = db.execute("SELECT cash, name, number FROM property WHERE id = ?", session["user_id"])[0]
        buy = db.execute("SELECT origin, destination, vehicle FROM buy WHERE id = ? AND exist = ?", session["user_id"], 1)

        # rendering profile page
        return render_template("profile.html", property=property, buy=buy)


@app.route("/history")
@login_required
def history():
 
    history_list = []

    # get datas from database
    buy = db.execute("SELECT year, month, day, hour, minute, vehicle, origin, destination FROM buy WHERE id = ? ORDER BY minute, hour, day, month, year DESC", session["user_id"])
    refund = db.execute("SELECT year, month, day, hour, minute, vehicle, origin, destination FROM refund  WHERE id = ? ORDER BY minute, hour, day, month, year DESC", session["user_id"])

    # add to list and dict
   
    for temp in buy:
        history_dict = {}
        history_dict["origin"] = temp["origin"]
        history_dict["destination"] = temp["destination"]
        history_dict["vehicle"] = temp["vehicle"]
        history_dict["year"] = temp["year"]
        history_dict["month"] = temp["month"]
        history_dict["day"] = temp["day"]
        history_dict["hour"] = temp["hour"]
        history_dict["minute"] = temp["minute"]
        history_dict["kind"] = "Buy"
        history_list.append(history_dict)

    for temp in refund:
        history_dict = {}
        history_dict["origin"] = temp["origin"]
        history_dict["destination"] = temp["destination"]
        history_dict["vehicle"] = temp["vehicle"]
        history_dict["year"] = temp["year"]
        history_dict["month"] = temp["month"]
        history_dict["day"] = temp["day"]
        history_dict["hour"] = temp["hour"]
        history_dict["minute"] = temp["minute"]
        history_dict["kind"] = "Refund"
        history_list.append(history_dict)

    # rendering history page
    return render_template("history.html", history=history_list)
        
        
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))


        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
    


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST
    if request.method == "POST":

        # get data from html page
        username = request.form.get("username")
        password = request.form.get("password")
        color = request.form.get("color")
        number = request.form.get("number")

        # check to enter username & password
        if not username:
            return apology("Please enter username")
        if not password:
            return apology("Please enter password")

        # insert datas to users table
        db.execute("INSERT INTO users (username, password, color, number) VALUES (?, ?, ?, ?)", username, password, color, number)

        # redirecting to homepage
        return redirect("/login")

    # User reached route via GET
    else:
        # rendering register
        return render_template("register.html")

    
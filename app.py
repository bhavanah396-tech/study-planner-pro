from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "studyflow"

# DATABASE
def db():
    return sqlite3.connect("database.db")

# INIT DATABASE
def init():

    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        date TEXT,
        time TEXT,
        priority INTEGER,
        duration INTEGER,
        status TEXT
    )
    """)

    conn.commit()

    c.execute("SELECT * FROM users WHERE username='admin'")
    admin = c.fetchone()

    if not admin:

        c.execute("""
        INSERT INTO users(username,email,password,role)
        VALUES(?,?,?,?)
        """,
        (
            "admin",
            "admin@gmail.com",
            "admin123",
            "admin"
        ))

    conn.commit()
    conn.close()

init()

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        conn = db()
        c = conn.cursor()

        c.execute("""
        SELECT * FROM users
        WHERE username=? AND password=?
        """,
        (
            request.form["username"],
            request.form["password"]
        ))

        user = c.fetchone()

        if user:

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[4]

            if user[4] == "admin":
                return redirect("/admin")

            return redirect("/dashboard")

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        conn = db()
        c = conn.cursor()

        c.execute("""
        INSERT INTO users(username,email,password,role)
        VALUES(?,?,?,?)
        """,
        (
            request.form["username"],
            request.form["email"],
            request.form["password"],
            "student"
        ))

        conn.commit()

        return redirect("/")

    return render_template("register.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():

    conn = db()
    c = conn.cursor()

    c.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE user_id=?
    """, (session["user_id"],))

    total = c.fetchone()[0]

    c.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE user_id=?
    AND status='done'
    """, (session["user_id"],))

    done = c.fetchone()[0]

    progress = 0

    if total > 0:
        progress = int((done/total)*100)

    c.execute("""
    SELECT id,title,description,date,time,status
    FROM tasks
    WHERE user_id=?
    ORDER BY id DESC
    """, (session["user_id"],))

    recent = c.fetchall()

    return render_template(
        "dashboard.html",
        username=session["username"],
        progress=progress,
        total=total,
        done=done,
        recent=recent
    )

# PLANNER
@app.route("/planner", methods=["GET","POST"])
def planner():

    if request.method == "POST":

        conn = db()
        c = conn.cursor()

        c.execute("""
        INSERT INTO tasks(
            user_id,
            title,
            description,
            date,
            time,
            priority,
            duration,
            status
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            session["user_id"],
            request.form["title"],
            request.form["description"],
            request.form["date"],
            request.form["time"],
            request.form["priority"],
            request.form["duration"],
            "pending"
        ))

        conn.commit()

        return redirect("/calendar")

    return render_template("planner.html")

# TASKS API
@app.route("/tasks")
def tasks():

    conn = db()
    c = conn.cursor()

    c.execute("""
    SELECT *
    FROM tasks
    WHERE user_id=?
    """, (session["user_id"],))

    rows = c.fetchall()

    data = []

    for r in rows:

        data.append({
            "id": r[0],
            "title": r[2],
            "start": r[4] + "T" + r[5],
            "description": r[3],
            "color": "#2563eb"
        })

    return jsonify(data)

# COMPLETE TASK
@app.route("/complete/<int:id>")
def complete(id):

    conn = db()
    c = conn.cursor()

    c.execute("""
    UPDATE tasks
    SET status='done'
    WHERE id=?
    """, (id,))

    conn.commit()

    return redirect("/dashboard")

# UPDATE TASK
@app.route("/update_task", methods=["POST"])
def update_task():

    data = request.json

    conn = db()
    c = conn.cursor()

    c.execute("""
    UPDATE tasks
    SET date=?, time=?
    WHERE id=?
    """,
    (
        data["date"],
        data["time"],
        data["id"]
    ))

    conn.commit()

    return "ok"

# CALENDAR
@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

# ANALYTICS
@app.route("/analytics")
def analytics():

    conn = db()
    c = conn.cursor()

    c.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status='done'
    """)

    done = c.fetchone()[0]

    c.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status='pending'
    """)

    pending = c.fetchone()[0]

    return render_template(
        "analytics.html",
        done=done,
        pending=pending
    )

# ADMIN
@app.route("/admin")
def admin():

    conn = db()
    c = conn.cursor()

    c.execute("""
    SELECT id,username,email
    FROM users
    WHERE role='student'
    """)

    users = c.fetchall()

    c.execute("""
    SELECT tasks.id,
           users.username,
           tasks.title,
           tasks.status
    FROM tasks
    JOIN users
    ON tasks.user_id = users.id
    """)

    tasks = c.fetchall()

    c.execute("""
    SELECT users.username,
           COUNT(tasks.id)
    FROM users
    LEFT JOIN tasks
    ON users.id = tasks.user_id
    AND tasks.status='done'
    GROUP BY users.username
    ORDER BY COUNT(tasks.id) DESC
    """)

    leaderboard = c.fetchall()

    return render_template(
        "admin.html",
        users=users,
        tasks=tasks,
        leaderboard=leaderboard
    )

# DELETE USER
@app.route("/delete_user/<int:id>")
def delete_user(id):

    conn = db()
    c = conn.cursor()

    c.execute("""
    DELETE FROM users
    WHERE id=?
    """, (id,))

    conn.commit()

    return redirect("/admin")

# DELETE TASK
@app.route("/delete_task/<int:id>")
def delete_task(id):

    conn = db()
    c = conn.cursor()

    c.execute("""
    DELETE FROM tasks
    WHERE id=?
    """, (id,))

    conn.commit()

    return redirect("/admin")

# DYNAMIC PROGRAMMING OPTIMIZER
@app.route("/optimize", methods=["GET","POST"])
def optimize():

    result = []

    if request.method == "POST":

        available = int(request.form["hours"])

        conn = db()
        c = conn.cursor()

        c.execute("""
        SELECT title,duration,priority
        FROM tasks
        WHERE user_id=?
        AND status='pending'
        """, (session["user_id"],))

        tasks = c.fetchall()

        n = len(tasks)

        dp = [[0 for x in range(available + 1)]
              for x in range(n + 1)]

        for i in range(1, n + 1):

            title, duration, priority = tasks[i-1]

            duration = int(duration)
            priority = int(priority)

            for w in range(available + 1):

                if duration <= w:

                    dp[i][w] = max(
                        priority + dp[i-1][w-duration],
                        dp[i-1][w]
                    )

                else:
                    dp[i][w] = dp[i-1][w]

        w = available

        for i in range(n, 0, -1):

            if dp[i][w] != dp[i-1][w]:

                result.append(tasks[i-1])

                w -= int(tasks[i-1][1])

    return render_template(
        "optimize.html",
        result=result
    )

# AUTO RESCHEDULE
@app.before_request
def reschedule():

    conn = db()
    c = conn.cursor()

    today = datetime.now().date()

    c.execute("""
    SELECT id,date
    FROM tasks
    WHERE status='pending'
    """)

    rows = c.fetchall()

    for r in rows:

        d = datetime.strptime(r[1], "%Y-%m-%d").date()

        if d < today:

            new_date = d + timedelta(days=7)

            c.execute("""
            UPDATE tasks
            SET date=?
            WHERE id=?
            """, (str(new_date), r[0]))

    conn.commit()

app.run(debug=True)
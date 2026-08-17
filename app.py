from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "task-management-secret-key")

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["task_management"]
users_collection = db["users"]
tasks_collection = db["tasks"]


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        existing_user = users_collection.find_one({"email": email})

        if existing_user:
            return "Email already registered. Please login."

        hashed_password = generate_password_hash(password)

        result = users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password
        })

        session["user_id"] = str(result.inserted_id)
        session["user_name"] = name

        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        return "Invalid email or password."

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    tasks = list(tasks_collection.find({"user_id": user_id}))

    return render_template(
        "dashboard.html",
        tasks=tasks,
        user_name=session.get("user_name")
    )


@app.route("/add_task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"].strip()
    description = request.form["description"].strip()

    if title:
        tasks_collection.insert_one({
            "user_id": ObjectId(session["user_id"]),
            "title": title,
            "description": description,
            "status": "Pending"
        })

    return redirect(url_for("dashboard"))


@app.route("/update_task/<task_id>", methods=["POST"])
def update_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"].strip()
    description = request.form["description"].strip()
    status = request.form["status"]

    tasks_collection.update_one(
        {
            "_id": ObjectId(task_id),
            "user_id": ObjectId(session["user_id"])
        },
        {
            "$set": {
                "title": title,
                "description": description,
                "status": status
            }
        }
    )

    return redirect(url_for("dashboard"))


@app.route("/delete_task/<task_id>", methods=["POST"])
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    tasks_collection.delete_one({
        "_id": ObjectId(task_id),
        "user_id": ObjectId(session["user_id"])
    })

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
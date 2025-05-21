import mysql.connector
import tkinter as tk
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Connect to MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",  # Replace with MySQL username
    password="changeme",  # Replace with MySQL password
    database="habit_tracker_db"
)
cursor = conn.cursor()

# Function to add a habit
def add_habit():
    habit = habit_entry.get()
    if habit:
        cursor.execute("INSERT INTO habits (habit_name, completed_dates) VALUES (%s, '')", (habit,))
        conn.commit()
        habit_listbox.insert(tk.END, habit)
        habit_entry.delete(0, tk.END)

# Function to mark habit as completed
def mark_completed():
    selected = habit_listbox.curselection()
    if selected:
        habit = habit_listbox.get(selected[0])
        cursor.execute("UPDATE habits SET completed_dates = CONCAT(completed_dates, ', ', CURDATE()) WHERE habit_name = %s", (habit,))
        conn.commit()
        message_label.config(text=f"Marked '{habit}' as completed today!")

# Fetch habit history for AI model
def get_habit_data():
    cursor.execute("SELECT habit_name, completed_dates FROM habits")
    data = cursor.fetchall()
    habit_list = []
    labels = []

    for habit_name, dates in data:
        history = dates.split(", ") if dates else []
        success_count = len(history)
        success_rate = success_count / 5 if success_count >= 5 else 0  # Normalize for past 5 days
        habit_list.append([success_count])
        labels.append(1 if success_rate >= 0.6 else 0)  # AI model: 1 = success, 0 = failure

    return np.array(habit_list), np.array(labels)

# Train AI Model
habit_data, habit_labels = get_habit_data()
if len(set(habit_labels)) >= 2:  # Ensure at least two distinct classes
    model = LogisticRegression()
    model.fit(habit_data, habit_labels)

# Predict habit success
def predict_success():
    cursor.execute("SELECT habit_name, completed_dates FROM habits")
    data = cursor.fetchall()

    if not data:
        prediction_label.config(text="No habits to predict.")
    else:
        habit_name, dates = data[0]  # Predict first habit (modify if needed)
        success_count = len(dates.split(", ")) if dates else 0
        prediction = model.predict([[success_count]])[0] if len(set(habit_labels)) >= 2 else 0
        result = f"Prediction for '{habit_name}': {'Likely to succeed!' if prediction == 1 else 'Stay motivated!'}"
        prediction_label.config(text=result)

# UI Setup
root = tk.Tk()
root.title("AI-Powered Habit Tracker")

habit_label = tk.Label(root, text="Enter Habit:")
habit_label.pack()

habit_entry = tk.Entry(root)
habit_entry.pack()

add_button = tk.Button(root, text="Add Habit", command=add_habit)
add_button.pack()

habit_listbox = tk.Listbox(root)
habit_listbox.pack()

complete_button = tk.Button(root, text="Mark as Completed", command=mark_completed)
complete_button.pack()

message_label = tk.Label(root, text="")
message_label.pack()

predict_button = tk.Button(root, text="Predict Habit Success", command=predict_success)
predict_button.pack()

prediction_label = tk.Label(root, text="Prediction will appear here")
prediction_label.pack()

root.mainloop()

# Close database connection
cursor.close()
conn.close()
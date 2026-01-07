try:
    from tkinter.messagebox import showinfo, showerror, askyesno
    import tkinter as tk
    from tkinter import filedialog
    import csv
    import customtkinter as ctk
    from customtkinter import (
        CTkButton, CTkLabel, CTkCheckBox, CTkEntry,
        CTkFrame, CTkScrollableFrame, CTkTabview,
        CTkComboBox, CTkTextbox, CTkToplevel
    )
    from typing import *
    from tkinter import messagebox
    import mysql.connector
    from datetime import date, datetime
    from tkcalendar import DateEntry
    from PIL import Image, ImageTk

except (ImportError, ModuleNotFoundError) as Error:
    quit(f"Missing Modules: {Error}")

# __________________ DATABASE CONNECTION LOGIC ________________________#

myDB = None
myCursor = None
DB_CONNECTED = False

try:
    myDB = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="testing"
    )
    myCursor = myDB.cursor()
    DB_CONNECTED = True
    print("--- SUCCESS: Connected to 'testing' Database ---")

except Exception as e:
    print(f"--- CRITICAL ERROR: Database connection failed. ---")
    print(f"Error: {e}")
    DB_CONNECTED = False

# __________________ AUTO-SETUP TABLES ________________________#
def initialize_database():
    """
    Checks if the required database tables exist.
    If they do not exist, it creates them automatically with the correct columns.
    :return: None
    """
    if not DB_CONNECTED:
        return

    try:
        # 1. Archive Books Table (Updated with AISLE)
        myCursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_books (
            ARCHIVE_ID INT AUTO_INCREMENT PRIMARY KEY,
            ORIGINAL_ID INT,
            TITLE VARCHAR(255),
            AUTHOR VARCHAR(255),
            AISLE VARCHAR(50),
            PUBLISHED_DATE VARCHAR(255),
            PUBLISHER VARCHAR(255),
            CATEGORY VARCHAR(255),
            ARCHIVED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. Curio Table (Trivia/Announcements)
        myCursor.execute("""
        CREATE TABLE IF NOT EXISTS curio (
            CURIO_ID INT AUTO_INCREMENT PRIMARY KEY,
            TITLE VARCHAR(255),
            TYPE VARCHAR(50),
            PUBLISHED_DATE DATE,
            VISIBILITY VARCHAR(50),
            CONTENT TEXT,
            ANSWER VARCHAR(255)
        )
        """)

        # 3. Students Table (Active Records)
        myCursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            STUDENT_NUMBER VARCHAR(50) UNIQUE,
            NAME VARCHAR(255)
        )
        """)

        # 4. Archived Students Table
        myCursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_students (
            ARCHIVE_ID INT AUTO_INCREMENT PRIMARY KEY,
            ORIGINAL_STUDENT_NUMBER VARCHAR(50),
            NAME VARCHAR(255),
            ARCHIVED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 5. Attendance Logs Table
        myCursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_logs (
            LOG_ID INT AUTO_INCREMENT PRIMARY KEY,
            STUDENT_ID INT,
            TIME_IN DATETIME,
            TIME_OUT DATETIME,
            FOREIGN KEY (STUDENT_ID) REFERENCES students(ID) ON DELETE CASCADE
        )
        """)

        # 6. Books Table (Updated with AISLE)
        myCursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            BOOKID INT AUTO_INCREMENT PRIMARY KEY,
            TITLE VARCHAR(255),
            AUTHOR VARCHAR(255),
            AISLE VARCHAR(50),
            PUBLISHED_DATE VARCHAR(255),
            PUBLISHER VARCHAR(255),
            CATEGORY VARCHAR(255)
        )
        """)

        myDB.commit()
        print("--- SYSTEM: Database Tables checked/created successfully ---")
    except Exception as e:
        print(f"Error creating tables: {e}")

initialize_database()
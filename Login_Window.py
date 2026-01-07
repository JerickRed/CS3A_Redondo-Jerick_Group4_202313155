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
    from MIS import * ; from Database import *

except (ImportError, ModuleNotFoundError) as Error:
    quit(f"Missing Modules: {Error}")

class Login(MIS):
    # ================= LOGIN LOGIC (MATCHING DESIGN) ================= #
    def drawLoginScreen(self):
        """
        Draws the login screen interface.
        :return: None
        """

        self.login_container = ctk.CTkFrame(self.master, fg_color=self.CONTENT_BG_COLOR, corner_radius=0)
        self.login_container.pack(fill="both", expand=True)

        self.login_sidebar = ctk.CTkFrame(self.login_container, width=350, fg_color=self.SIDEBAR_COLOR, corner_radius=0)
        self.login_sidebar.pack(side="left", fill="y")
        self.login_sidebar.pack_propagate(False)  # Force width

        self.login_content = ctk.CTkFrame(self.login_container, fg_color=self.CONTENT_BG_COLOR, corner_radius=0)
        self.login_content.pack(side="right", fill="both", expand=True)

        # --- LEFT SIDE WIDGETS ---

        # Title
        ctk.CTkLabel(self.login_sidebar, text="LIBRARY MIS", font=("Agency FB", 40, "bold"),
                     text_color="#D9F9D4").pack(pady=(50, 5))
        ctk.CTkLabel(self.login_sidebar, text="BY: CS3A", font=("Agency FB", 16),
                     text_color="gray").pack(pady=(0, 60))

        # Inputs Container
        input_frame = ctk.CTkFrame(self.login_sidebar, fg_color="transparent")
        input_frame.pack(fill="x", padx=30)

        # Username
        ctk.CTkLabel(input_frame, text="USERNAME", font=("Agency FB", 20), text_color="#D9F9D4", anchor="w").pack(
            fill="x")
        self.entry_user = ctk.CTkEntry(input_frame, height=40, border_width=0, fg_color="#A0A0A0", text_color="black")
        self.entry_user.pack(fill="x", pady=(5, 20))

        # Password
        ctk.CTkLabel(input_frame, text="PASSWORD", font=("Agency FB", 20), text_color="#D9F9D4", anchor="w").pack(
            fill="x")
        self.entry_pass = ctk.CTkEntry(input_frame, height=40, border_width=0, fg_color="#A0A0A0", text_color="black",
                                       show="*")
        self.entry_pass.pack(fill="x", pady=(5, 40))

        # Login Button
        self.btn_login = ctk.CTkButton(input_frame, text="LOGIN", height=45,
                                       fg_color=self.MAIN_BG_COLOR, font=("Arial", 14, "bold"),
                                       hover_color="#3E5F33", command=self.verify_login)
        self.btn_login.pack(fill="x")

        ctk.CTkLabel(self.login_sidebar, text=f"DB: {'Connected' if DB_CONNECTED else 'Disconnected'}",
                     font=("Arial", 10), text_color="white").pack(side="bottom", pady=20)

        right_center_frame = ctk.CTkFrame(self.login_content, fg_color="transparent")
        right_center_frame.place(relx=0.5, rely=0.5, anchor="center")

        try:
            # creates the background image for the login screen to use
            pil_image = Image.open("CVSU.png")
            img_obj = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(600, 400))

            border_frame = ctk.CTkFrame(right_center_frame, fg_color=self.SIDEBAR_COLOR, corner_radius=0)
            border_frame.pack(pady=10)

            img_label = ctk.CTkLabel(border_frame, image=img_obj, text="")
            img_label.pack(padx=5, pady=5)

        except Exception as e:
            ctk.CTkLabel(right_center_frame, text=f"Image 'CVSU.png' not found.\n{e}", text_color="red").pack()

        ctk.CTkLabel(right_center_frame, text="CAVITE CITY CAMPUS", font=("Arial", 30, "bold"),
                     text_color=self.SIDEBAR_COLOR).pack(pady=10)

        self.master.bind('<Return>', lambda event: self.verify_login())

    def verify_login(self):
        """
        Verifies the user credentials against hardcoded values.
        :return: None
        """
        username = self.entry_user.get()
        password = self.entry_pass.get()

        if (username == "admin" and password == "123") or (username == "user" and password == "password"):
            self.launch_main_system()
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password.")

    def launch_main_system(self):
        """
        Transitions from the login screen to the main application dashboard.
        :return: None
        """
        self.login_container.destroy()
        self.background1.pack(fill="both", expand=True)
        self.placeObjects()
        self.master.unbind('<Return>')

    # ================= END LOGIN LOGIC ================= #
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
    from Database import *
    import random

except (ImportError, ModuleNotFoundError) as Error:
    quit(f"Missing Modules: {Error}")


# _____________________________________________________________________#

# noinspection PyMethodMayBeStatic
class MIS:
    # creates the window where the objects and interactibles will be drawn onto
    master = ctk.CTk()
    master.geometry("1340x700")
    master.resizable(False, False)
    master.title("Library Management System")

    SIDEBAR_COLOR: str = "#30443B"
    CONTENT_BG_COLOR: str = "#D9F9D4"
    MAIN_BG_COLOR: str = "#4F7942"
    ACTIVE_BUTTON_COLOR: str = "#4F7942"

    def __init__(self) -> None:
        if not DB_CONNECTED:
            messagebox.showerror("Connection Error",
                                 "Could not connect to the Database 'testing'.\nPlease check HeidiSQL/xampp.")

        self.edit_mode_id = None
        self.checkbox_states = {}
        self.book_ids_map = {}

        # Archive Selection Tracking
        self.archive_book_vars = {}
        self.archive_book_ids = {}
        self.archive_student_vars = {}
        self.archive_student_ids = {}

        # Curio editing tracking
        self.curio_db_map = {}
        self.editing_curio_id = None
        self.curio_timer = None

        # Student editing tracking
        self.student_edit_id = None

        # --- PAGINATION VARIABLES ---
        self.current_page = 1
        self.items_per_page = 20
        self.total_pages = 1
        self.current_data_cache = []  # Stores the full list to slice from

        # --- MAIN UI SETUP (Initially Hidden) ---
        self.background1 = CTkFrame(master=self.master, fg_color=self.MAIN_BG_COLOR, width=1340, height=700)

        self.sidebar_frame = ctk.CTkFrame(master=self.background1, width=250, height=700, fg_color=self.SIDEBAR_COLOR,
                                          corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_buttons = {}
        self.active_button = None
        self._draw_sidebar_content()

        self.bookTabs = CTkTabview(master=self.background1, width=1, height=1, corner_radius=20,
                                   segmented_button_fg_color=self.MAIN_BG_COLOR,
                                   segmented_button_selected_color=self.MAIN_BG_COLOR)
        self.bookTabs.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        self.bookTabs.add("HOME")
        self.bookTabs.add("LIST OF BOOKS")
        self.bookTabs.add("ARCHIVE")
        self.bookTabs.add("Borrow")
        self.bookTabs.add("History")
        self.hideTabButtons()

    def logout_system(self):
        confirm = messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?")
        if confirm:
            if self.curio_timer:
                self.master.after_cancel(self.curio_timer)
                self.curio_timer = None

            self.background1.pack_forget()
            if self.active_button:
                self.active_button.configure(fg_color="transparent")
                self.active_button = None

            if hasattr(self, 'drawLoginScreen'):
                self.drawLoginScreen()

    def _draw_sidebar_content(self) -> None:
        # Top Labels
        CTkLabel(self.sidebar_frame, text="LIBRARY MIS", font=("Agency FB", 30, "bold"), text_color="#D9F9D4").pack(
            pady=(20, 5))
        CTkLabel(self.sidebar_frame, text="BY: CS3A", font=("Agency FB", 14), text_color="#A0A0A0").pack(pady=(0, 20))

        # Navigation Buttons
        menu_items = {
            "HOME": ("\uf015", "HOME"),
            "LIST OF BOOKS": ("\uf03a", "LIST OF BOOKS"),
            "ARCHIVE": ("\uf187", "ARCHIVE"),
            "CURIO": ("\uf059", "Borrow"),
            "RECORDS": ("\uf15c", "History")
        }

        for sidebar_text, (icon_char, tab_name) in menu_items.items():
            button = CTkButton(self.sidebar_frame, text=f"  {icon_char}   {sidebar_text}",
                               font=("Agency FB", 20), fg_color="transparent",
                               hover_color=self.ACTIVE_BUTTON_COLOR, anchor="w", width=200, height=40,
                               command=lambda name=tab_name: self.changeTab(name))

            button.pack(pady=5, padx=20)
            self.sidebar_buttons[tab_name] = button

        # --- BOTTOM CONTAINER (Status + Logout) ---
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        # FIXED: Using place to anchor to bottom of visible area
        bottom_frame.place(relx=0.5, rely=0.98, anchor="s", relwidth=0.85)

        status_text = "DB: Connected" if DB_CONNECTED else "DB: Disconnected"
        status_color = "#D9F9D4" if DB_CONNECTED else "red"
        CTkLabel(bottom_frame, text=status_text, text_color=status_color,
                 font=("Arial", 12, "bold")).pack(side="bottom", pady=(5, 0))

        logout_btn = CTkButton(bottom_frame, text="  \uf08b   LOGOUT",
                               font=("Agency FB", 20), fg_color="#C0392B",
                               hover_color="#922B21", anchor="w", height=40,
                               command=self.logout_system)
        logout_btn.pack(side="bottom", fill="x")

    def changeTab(self, tab_name: str) -> None:
        if self.curio_timer:
            self.master.after_cancel(self.curio_timer)
            self.curio_timer = None

        if self.active_button: self.active_button.configure(fg_color="transparent")
        new_active_button = self.sidebar_buttons.get(tab_name)
        if new_active_button:
            new_active_button.configure(fg_color=self.ACTIVE_BUTTON_COLOR)
            self.active_button = new_active_button

        self.bookTabs.set(tab_name)
        if tab_name == "HOME": self.drawDashboard()
        if tab_name == "LIST OF BOOKS": self.refresh_list_table()
        if tab_name == "ARCHIVE": self.refresh_archive_table()
        if tab_name == "Borrow": self.drawBorrowTab()
        if tab_name == "History": self.drawHistoryTab()

    def hideTabButtons(self) -> None:
        try:
            self.bookTabs._segmented_button.grid_remove()
        except:
            pass

    # __________________ HELPER: FETCH DATA (UPDATED FOR SORTING) __________________ #
    def fetch_data(self, query_type, sort_by="TITLE"):
        if not DB_CONNECTED:
            return []

        try:
            if query_type == "active_books":
                # Ensure the sort_by column is safe to use in SQL
                valid_cols = {"TITLE", "AUTHOR", "AISLE", "PUBLISHED_DATE", "PUBLISHER", "CATEGORY"}
                order_col = sort_by if sort_by in valid_cols else "TITLE"

                # Fetch data sorted by the user's choice
                query = f"SELECT BOOKID, TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY FROM books ORDER BY {order_col}, TITLE"
                myCursor.execute(query)
                rows = myCursor.fetchall()

                formatted_data = []
                for r in rows:
                    formatted_data.append((
                        r[0], r[1] or "", r[2] or "", r[3] or "",
                        r[4] or "", r[5] or "", r[6] or ""
                    ))
                return formatted_data

            elif query_type == "archived_books":
                # Updated to fetch Aisle
                myCursor.execute(
                    "SELECT ORIGINAL_ID, TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY, ARCHIVED_DATE, ARCHIVE_ID FROM archived_books ORDER BY TITLE")
                return myCursor.fetchall()

            elif query_type == "curio_list":
                myCursor.execute("SELECT CURIO_ID, TITLE, TYPE, PUBLISHED_DATE, VISIBILITY, CONTENT, ANSWER FROM curio")
                return myCursor.fetchall()

            elif query_type == "records":
                myCursor.execute("SELECT ID, STUDENT_NUMBER, NAME FROM students ORDER BY ID ASC")
                return myCursor.fetchall()

            elif query_type == "archived_students":
                myCursor.execute(
                    "SELECT ARCHIVE_ID, ORIGINAL_STUDENT_NUMBER, NAME, ARCHIVED_DATE FROM archived_students")
                return myCursor.fetchall()

        except Exception as e:
            print(f"Error fetching {query_type}: {e}")
            return []
        return []

    # __________________ DASHBOARD __________________ #
    def check_suggestions(self, event) -> None:
        typed_text = self.search_entry.get().lower()
        if not typed_text:
            try:
                self.suggestion_frame.place_forget()
            except:
                pass
            return
        all_data = self.fetch_data("active_books")
        matches = [str(book[1]) for book in all_data if typed_text in str(book[1]).lower()]
        self.update_suggestion_box(matches)

    def update_suggestion_box(self, matches: List[str]) -> None:
        if not hasattr(self, 'suggestion_frame'): return
        for widget in self.suggestion_frame.winfo_children(): widget.destroy()
        if not matches:
            self.suggestion_frame.place_forget()
            return
        self.suggestion_frame.place(relx=0.5, y=155, anchor="n")
        self.suggestion_frame.lift()
        for item in matches:
            CTkButton(self.suggestion_frame, text=item, font=("Arial", 14), anchor="w",
                      fg_color="transparent", text_color="black", hover_color="#E0E0E0", height=30,
                      command=lambda v=item: self.select_suggestion(v)).pack(fill="x", padx=5, pady=2)

    def select_suggestion(self, value: str) -> None:
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, value)
        self.suggestion_frame.place_forget()
        self.perform_search(value)

    def perform_search(self, query: str) -> None:
        try:
            self.suggestion_frame.place_forget()
        except:
            pass
        if not query.strip(): self.changeTab("LIST OF BOOKS"); return

        all_data = self.fetch_data("active_books", sort_by="TITLE")
        results = [book for book in all_data if query.lower() in str(book[1]).lower()]

        if results:
            self.changeTab("LIST OF BOOKS")
            self.refresh_list_table(custom_data=results)
        else:
            showinfo("No Results", f"No books found matching: '{query}'")

    def drawDashboard(self) -> None:
        tab = self.bookTabs.tab("HOME")
        tab.configure(fg_color="transparent")
        for w in tab.winfo_children(): w.destroy()

        content = ctk.CTkFrame(tab, fg_color=self.CONTENT_BG_COLOR, corner_radius=20)
        content.pack(padx=1, pady=1, fill="both", expand=True)

        CTkLabel(content, text="DASHBOARD", font=("Agency FB", 35, "bold"), text_color=self.SIDEBAR_COLOR).pack(
            pady=(40, 20))

        search_frame = CTkFrame(content, fg_color="white", corner_radius=10, width=500, height=40)
        search_frame.pack(pady=(0, 20))
        search_frame.pack_propagate(False)

        self.search_entry = CTkEntry(search_frame, placeholder_text="Search by title",
                                     width=480, height=30, corner_radius=10, border_width=0,
                                     text_color=self.SIDEBAR_COLOR, fg_color="white")
        self.search_entry.place(relx=0.5, rely=0.5, anchor="center")
        self.search_entry.bind("<KeyRelease>", self.check_suggestions)
        self.search_entry.bind("<Return>", lambda event: self.perform_search(self.search_entry.get()))

        self.suggestion_frame = CTkScrollableFrame(content, width=450, height=150, fg_color="white",
                                                   corner_radius=10, border_width=1, border_color="gray")

        active_data = self.fetch_data("active_books")
        records_data = self.fetch_data("records")
        topics = set()
        if active_data:
            for row in active_data:
                if len(row) > 6: topics.add(row[6])

        # --- STATS CARDS ---
        cards_container = ctk.CTkFrame(content, fg_color="transparent")
        cards_container.pack(pady=20)

        stats_map = {
            "TOTAL BOOKS": str(len(active_data)),
            "CATEGORIES": str(len(topics)),
            "STUDENTS": str(len(records_data))
        }

        for label_text, val in stats_map.items():
            card = ctk.CTkFrame(cards_container, width=200, height=200, fg_color="#C0C0C0", corner_radius=20)
            card.pack(side="left", padx=30)
            card.pack_propagate(False)
            CTkLabel(card, text=val, font=("Agency FB", 60, "bold"), text_color=self.SIDEBAR_COLOR).place(relx=0.5,
                                                                                                          rely=0.4,
                                                                                                          anchor="center")
            CTkLabel(card, text=label_text, font=("Agency FB", 20, "bold"), text_color=self.SIDEBAR_COLOR).place(
                relx=0.5, rely=0.75, anchor="center")

        # --- CURIO SECTION ---
        self.curio_frame = ctk.CTkFrame(content, fg_color="#8FBC8F", corner_radius=15, height=150)
        self.curio_frame.pack(fill="x", padx=50, pady=(20, 20))
        self.curio_frame.pack_propagate(False)
        self.update_dashboard_curio()

    def update_dashboard_curio(self):
        if self.curio_timer:
            self.master.after_cancel(self.curio_timer)
        for w in self.curio_frame.winfo_children(): w.destroy()
        curios = self.fetch_data("curio_list")
        if not curios:
            CTkLabel(self.curio_frame, text="Did You Know?", font=("Agency FB", 24, "bold"), text_color="white").pack(
                pady=(10, 0))
            CTkLabel(self.curio_frame, text="No curios/trivia available in database.", text_color="white").pack(pady=10)
        else:
            selected = random.choice(curios)
            c_title, c_type, c_content, c_answer = selected[1], selected[2], selected[5], selected[6]
            header_text = f"TRIVIA: {c_title}" if c_type == "Trivia" else f"{c_type.upper()}: {c_title}"
            CTkLabel(self.curio_frame, text=header_text, font=("Agency FB", 24, "bold"), text_color="white").pack(
                pady=(10, 5))
            CTkLabel(self.curio_frame, text=c_content, font=("Arial", 16), text_color="white", wraplength=800).pack(
                pady=5)
            if c_type == "Trivia" and c_answer:
                ans_lbl = CTkLabel(self.curio_frame, text=f"Answer: {c_answer}", font=("Arial", 14, "bold"),
                                   text_color="#2E4053")
                btn = CTkButton(self.curio_frame, text="Reveal Answer", height=25, width=100,
                                fg_color="#F39C12", hover_color="#D35400",
                                command=lambda: [btn.pack_forget(), ans_lbl.pack(pady=5)])
                btn.pack(pady=5)
        self.curio_timer = self.master.after(random.randint(300000, 600000), self.update_dashboard_curio)

    # __________________ LIST OF BOOKS (UPDATED FOR SORTING & PAGINATION) __________________ #
    def listBooks(self) -> None:
        tab = self.bookTabs.tab("LIST OF BOOKS")
        tab.configure(fg_color="transparent")
        if len(tab.winfo_children()) > 0: return

        self.list_inner_tabs = ctk.CTkTabview(master=tab, fg_color=self.CONTENT_BG_COLOR, corner_radius=20, height=500)
        self.list_inner_tabs.pack(padx=1, pady=1, fill="both", expand=True)
        self.list_inner_tabs.add("List of books")
        self.list_inner_tabs.add("Manage Book")

        self._draw_manage_form()

        # Controls Container
        controls = CTkFrame(self.list_inner_tabs.tab("List of books"), fg_color="transparent", height=40)
        controls.pack(fill="x", padx=30, pady=(10, 0))

        # --- LEFT SIDE CONTROLS ---
        self.select_all_var = tk.IntVar(value=0)
        CTkCheckBox(controls, text="Select All", variable=self.select_all_var, command=self.toggle_select_all,
                    text_color="black").pack(side="left", padx=10)
        self.lbl_count = CTkLabel(controls, text="0 Selected", text_color="black", font=("Arial", 12, "bold"))
        self.lbl_count.pack(side="left", padx=10)

        # --- RIGHT SIDE CONTROLS (ARCHIVE + SORTER) ---
        self.btn_archive = CTkButton(controls, text="ARCHIVE SELECTED", fg_color="red", state="disabled",
                                     command=self.archive_selected)
        self.btn_archive.pack(side="right", padx=(10, 0))

        # 1. Filter/Sort Entry
        self.filter_entry = CTkEntry(controls, placeholder_text="Type to find...", width=180)
        self.filter_entry.pack(side="right", padx=5)
        self.filter_entry.bind("<KeyRelease>", self.apply_sort_and_filter)

        # 2. Sort Dropdown
        self.sort_type = CTkComboBox(controls, values=["Title", "Author", "Aisle", "Year", "Publisher", "Category"],
                                     width=110,
                                     command=self.apply_sort_and_filter)
        self.sort_type.set("Title")
        self.sort_type.pack(side="right", padx=5)

        CTkLabel(controls, text="Sort By:", text_color="black", font=("Arial", 12, "bold")).pack(side="right", padx=5)

        self.table_frame = CTkScrollableFrame(self.list_inner_tabs.tab("List of books"), fg_color="ivory4",
                                              corner_radius=25)
        self.table_frame.pack(padx=30, pady=10, fill="both", expand=True)

        # --- PAGINATION CONTROLS (BOTTOM) ---
        self.pagination_frame = CTkFrame(self.list_inner_tabs.tab("List of books"), fg_color="transparent", height=40)
        self.pagination_frame.pack(fill="x", padx=30, pady=(5, 10))

        self.btn_prev = CTkButton(self.pagination_frame, text="< PREVIOUS", width=100,
                                  command=lambda: self.change_page(-1))
        self.btn_prev.pack(side="left")

        self.lbl_page = CTkLabel(self.pagination_frame, text="Page 1 of 1", font=("Arial", 12, "bold"),
                                 text_color="black")
        self.lbl_page.pack(side="left", expand=True)  # Centers it

        self.btn_next = CTkButton(self.pagination_frame, text="NEXT >", width=100, command=lambda: self.change_page(1))
        self.btn_next.pack(side="right")

        # Initial Load
        self.refresh_list_table()

    def change_page(self, direction):
        """
        Moves pagination forward or backward.
        """
        new_page = self.current_page + direction
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            # Refresh using the cached data (do not re-fetch from DB, just slice)
            self.refresh_list_table(use_cache=True)

    def apply_sort_and_filter(self, event=None):
        sort_selection = self.sort_type.get()
        search_text = self.filter_entry.get().lower()

        sort_map = {
            "Title": "TITLE",
            "Author": "AUTHOR",
            "Aisle": "AISLE",
            "Year": "PUBLISHED_DATE",
            "Publisher": "PUBLISHER",
            "Category": "CATEGORY"
        }
        db_col = sort_map.get(sort_selection, "TITLE")

        # 1. Fetch ALL sorted data from DB
        all_data = self.fetch_data("active_books", sort_by=db_col)

        idx_map = {
            "Title": 1, "Author": 2, "Aisle": 3,
            "Year": 4, "Publisher": 5, "Category": 6
        }
        self.grouping_idx = idx_map.get(sort_selection, 1)  # Store for grouping display

        # 2. Filter data
        if search_text:
            filtered_data = []
            for row in all_data:
                row_content = [str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6])]
                if any(search_text in col.lower() for col in row_content):
                    filtered_data.append(row)
        else:
            filtered_data = all_data

        # 3. Reset to Page 1 on new filter
        self.current_page = 1

        # 4. Refresh table
        self.refresh_list_table(custom_data=filtered_data)

    def _draw_manage_form(self):
        f = self.list_inner_tabs.tab("Manage Book")
        center_frame = ctk.CTkFrame(f, fg_color="transparent")
        center_frame.pack(expand=True)

        self.lbl_form_title = CTkLabel(center_frame, text="ADD NEW BOOK", font=("Agency FB", 25, "bold"),
                                       text_color="black")
        self.lbl_form_title.grid(row=0, column=1, pady=20)

        self.e_title = CTkEntry(center_frame, placeholder_text="Title", width=400)
        self.e_auth = CTkEntry(center_frame, placeholder_text="Author", width=400)
        self.e_aisle = CTkEntry(center_frame, placeholder_text="Aisle (e.g. A1)", width=400)
        self.e_date = CTkEntry(center_frame, placeholder_text="Date (YYYY-MM-DD)", width=400)
        self.e_pub = CTkEntry(center_frame, placeholder_text="Publisher", width=400)

        categories = ["Fiction", "Non-Fiction", "Science", "Technology", "History",
                      "Biography", "Arts", "Religion", "Philosophy", "Self-Help",
                      "Health", "Travel", "Guide", "Children", "Comics",
                      "Textbook", "Cookbook", "Memoir", "Poetry", "Reference", "Other"]
        self.e_topic = CTkComboBox(center_frame, values=categories, width=400)

        inputs = [("Title:", self.e_title), ("Author:", self.e_auth), ("Aisle:", self.e_aisle),
                  ("Date:", self.e_date), ("Pub:", self.e_pub), ("Category:", self.e_topic)]

        for i, (txt, e) in enumerate(inputs):
            CTkLabel(center_frame, text=txt, text_color="black").grid(row=i + 1, column=0, padx=20, pady=10, sticky="e")
            e.grid(row=i + 1, column=1, pady=10)

        btn_row = CTkFrame(center_frame, fg_color="transparent")
        btn_row.grid(row=7, column=1, pady=20)

        self.btn_save_update = CTkButton(btn_row, text="SAVE BOOK", fg_color=self.MAIN_BG_COLOR,
                                         command=self.save_or_update_book)
        self.btn_save_update.pack(side="left", padx=5)

        CTkButton(btn_row, text="IMPORT CSV", fg_color="#3498DB", command=self.import_csv_action).pack(side="left",
                                                                                                       padx=5)
        CTkButton(btn_row, text="RESET DATABASE", fg_color="#C0392B", command=self.nuclear_reset_books).pack(
            side="left", padx=5)

        CTkButton(center_frame, text="CANCEL / CLEAR FORM", fg_color="gray", command=self.clear_form).grid(row=8,
                                                                                                           column=1)

    def nuclear_reset_books(self):
        if not DB_CONNECTED: return
        if not messagebox.askyesno("WARNING",
                                   "This will DELETE ALL BOOKS and RESET THE STRUCTURE!\nAre you sure?"):
            return
        try:
            myCursor.execute("DROP TABLE IF EXISTS books")
            myCursor.execute("DROP TABLE IF EXISTS archived_books")
            myDB.commit()
            initialize_database()
            messagebox.showinfo("Success", "Tables Reset. You can now Import CSV.")
            self.refresh_list_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset: {e}")

    def import_csv_action(self):
        if not DB_CONNECTED:
            messagebox.showerror("Error", "No Database Connection.")
            return

        file_path = filedialog.askopenfilename(title="Select Books CSV", filetypes=[("CSV Files", "*.csv")])
        if not file_path: return

        success_count = 0
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 6:
                        title = row[0].strip()
                        if title.lower() == "title": continue

                        author = row[1].strip()
                        aisle = row[2].strip()
                        pub_date = row[3].strip()
                        publisher = row[4].strip()
                        category = row[5].strip()

                        if title:
                            query = "INSERT INTO books (TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY) VALUES (%s, %s, %s, %s, %s, %s)"
                            myCursor.execute(query, (title, author, aisle, pub_date, publisher, category))
                            success_count += 1
            myDB.commit()
            messagebox.showinfo("Import Success", f"Successfully imported {success_count} books.")
            self.refresh_list_table()
        except Exception as e:
            myDB.rollback()
            messagebox.showerror("Import Failed", f"Error reading CSV: {e}")

    def refresh_list_table(self, custom_data=None, grouping_col_idx=None, use_cache=False):
        """
        Refreshes the table with Pagination + Grouping.
        """
        if not hasattr(self, 'table_frame'): return
        for w in self.table_frame.winfo_children(): w.destroy()

        self.checkbox_states = {}
        self.book_ids_map = {}
        self.select_all_var.set(0)
        self.update_counter()

        # 1. Get Data source
        if use_cache:
            # Use previously stored list (allows paging without re-fetching)
            full_data = self.current_data_cache
        elif custom_data is not None:
            full_data = custom_data
            self.current_data_cache = custom_data  # Cache it
        else:
            full_data = self.fetch_data("active_books")
            self.current_data_cache = full_data  # Cache it

        # 2. Pagination Logic
        total_items = len(full_data)
        self.total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        if self.total_pages < 1: self.total_pages = 1

        # Ensure current page is valid
        if self.current_page > self.total_pages: self.current_page = self.total_pages
        if self.current_page < 1: self.current_page = 1

        # Slice Data
        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page
        page_data = full_data[start:end]

        # Update Pagination UI
        self.lbl_page.configure(text=f"Page {self.current_page} of {self.total_pages}")

        state_prev = "normal" if self.current_page > 1 else "disabled"
        state_next = "normal" if self.current_page < self.total_pages else "disabled"
        self.btn_prev.configure(state=state_prev)
        self.btn_next.configure(state=state_next)

        # 3. Draw Headers
        headers = ["SEL", "ID", "TITLE", "AUTHOR", "AISLE", "PUBLISHED", "PUBLISHER", "CATEGORY", "ACTION"]
        weights = [0, 0, 3, 2, 0, 0, 2, 1, 0]
        min_widths = [30, 30, 0, 0, 50, 80, 0, 0, 70]

        for c, h in enumerate(headers):
            self.table_frame.grid_columnconfigure(c, weight=weights[c])
            width_val = min_widths[c] if weights[c] == 0 else 0
            CTkLabel(self.table_frame, text=h, font=("Agency FB", 18, "bold"), text_color="black",
                     width=width_val, anchor="w").grid(row=0, column=c, padx=5, pady=10, sticky="ew")

        # 4. Draw Rows (Karaoke Grouping)
        current_group_value = None
        row_counter = 1

        # If use_cache was called, we need to know what grouping_idx was used previously
        # We can default to self.grouping_idx if it exists, otherwise use Title(1)
        if not hasattr(self, 'grouping_idx'): self.grouping_idx = 1
        active_group_idx = grouping_col_idx if grouping_col_idx is not None else self.grouping_idx

        for r, row in enumerate(page_data):
            # Karaoke Header Logic
            if active_group_idx != 1:  # If not sorting by Title
                val = str(row[active_group_idx]).upper()
                if val != current_group_value:
                    header_frame = ctk.CTkFrame(self.table_frame, fg_color="#30443B", corner_radius=5)
                    header_frame.grid(row=row_counter, column=0, columnspan=9, sticky="ew", pady=(10, 2))
                    CTkLabel(header_frame, text=f"  {val}", font=("Arial", 14, "bold"), text_color="white",
                             anchor="w").pack(fill="x", padx=10)
                    current_group_value = val
                    row_counter += 1

            bid = row[0]
            var = tk.IntVar(value=0)

            CTkCheckBox(self.table_frame, text="", variable=var, width=20, command=self.update_counter) \
                .grid(row=row_counter, column=0, padx=10, sticky="w")

            # Map original index from full_data if possible, but here r is 0-19.
            # Checkbox states usually need absolute index if you want "Select All" to work across pages.
            # But simplistic approach: checkbox states track VISIBLE rows for this page.
            self.checkbox_states[r] = var
            self.book_ids_map[r] = bid

            val_map = {1: row[0], 2: row[1], 3: row[2], 4: row[3], 5: row[4], 6: row[5], 7: row[6]}

            for col_idx, val_text in val_map.items():
                is_flexible = weights[col_idx] > 0
                wrap_val = 150 if is_flexible else 0
                CTkLabel(self.table_frame, text=str(val_text), font=("Agency FB", 18), text_color="black",
                         wraplength=wrap_val, anchor="w") \
                    .grid(row=row_counter, column=col_idx, padx=5, pady=5, sticky="ew")

            CTkButton(self.table_frame, text="EDIT", width=60, height=25, fg_color="#F39C12",
                      command=lambda d=row: self.load_edit_data(d)).grid(row=row_counter, column=8, padx=5, sticky="ew")

            row_counter += 1

    def load_edit_data(self, row_data):
        self.edit_mode_id = row_data[0]
        self.list_inner_tabs.set("Manage Book")
        self.lbl_form_title.configure(text=f"EDITING BOOK ID: {self.edit_mode_id}")
        self.btn_save_update.configure(text="UPDATE BOOK")

        entries = [self.e_title, self.e_auth, self.e_aisle, self.e_date, self.e_pub]
        db_vals = [row_data[1], row_data[2], row_data[3], row_data[4], row_data[5]]

        for i, e in enumerate(entries):
            e.delete(0, 'end')
            if len(db_vals) > i and db_vals[i] is not None:
                e.insert(0, str(db_vals[i]))

        if row_data[6]:
            self.e_topic.set(str(row_data[6]))
        else:
            self.e_topic.set("Fiction")

    def save_or_update_book(self):
        if not DB_CONNECTED:
            messagebox.showerror("Error", "No Database Connection.")
            return

        vals = (self.e_title.get(), self.e_auth.get(), self.e_aisle.get(), self.e_date.get(), self.e_pub.get(),
                self.e_topic.get())
        if not vals[0]: return messagebox.showerror("Error", "Title required")

        if self.edit_mode_id:
            query = "UPDATE books SET TITLE=%s, AUTHOR=%s, AISLE=%s, PUBLISHED_DATE=%s, PUBLISHER=%s, CATEGORY=%s WHERE BOOKID=%s"
            params = (*vals, self.edit_mode_id)
        else:
            query = "INSERT INTO books (TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY) VALUES (%s, %s, %s, %s, %s, %s)"
            params = vals

        try:
            myCursor.execute(query, params)
            myDB.commit()
            messagebox.showinfo("Success", "Book Saved")
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        self.edit_mode_id = None
        self.lbl_form_title.configure(text="ADD NEW BOOK")
        self.btn_save_update.configure(text="SAVE BOOK")
        for e in [self.e_title, self.e_auth, self.e_aisle, self.e_date, self.e_pub]: e.delete(0, 'end')
        self.e_topic.set("Fiction")
        self.list_inner_tabs.set("List of books")
        self.refresh_list_table()

    def update_counter(self):
        c = sum(v.get() for v in self.checkbox_states.values())
        self.lbl_count.configure(text=f"{c} Selected")
        if c > 0:
            self.btn_archive.configure(state="normal", fg_color="red")
        else:
            self.btn_archive.configure(state="disabled", fg_color="gray")

    def toggle_select_all(self):
        s = self.select_all_var.get()
        for v in self.checkbox_states.values(): v.set(s)
        self.update_counter()

    # __________________ ARCHIVE LOGIC (BOOKS & STUDENTS) __________________ #

    def archive_selected(self):
        if not DB_CONNECTED:
            messagebox.showerror("Error", "No Database Connection")
            return

        ids_to_archive = []
        for index, var in self.checkbox_states.items():
            if var.get() == 1:
                ids_to_archive.append(self.book_ids_map[index])

        if not ids_to_archive:
            return

        confirm = messagebox.askyesno("Confirm Archive",
                                      f"Are you sure you want to archive {len(ids_to_archive)} book(s)?")
        if not confirm:
            return

        success_count = 0
        try:
            for book_id in ids_to_archive:
                copy_query = """
                INSERT INTO archived_books (ORIGINAL_ID, TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY)
                SELECT BOOKID, TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY FROM books WHERE BOOKID = %s
                """
                myCursor.execute(copy_query, (book_id,))
                delete_query = "DELETE FROM books WHERE BOOKID = %s"
                myCursor.execute(delete_query, (book_id,))
                success_count += 1

            myDB.commit()
            messagebox.showinfo("Success", f"Archived {success_count} books.")
            self.refresh_list_table()
            self.refresh_archive_table()

        except Exception as e:
            myDB.rollback()
            messagebox.showerror("Error", f"Failed to archive: {e}")

    def refresh_archive_table(self):
        tab = self.bookTabs.tab("ARCHIVE")
        tab.configure(fg_color="transparent")

        if not hasattr(self, 'archive_tabs'):
            self.archive_tabs = ctk.CTkTabview(tab, fg_color=self.CONTENT_BG_COLOR, corner_radius=20)
            self.archive_tabs.pack(fill="both", expand=True, padx=20, pady=20)
            self.archive_tabs.add("Archived Books")
            self.archive_tabs.add("Archived Students")

            # --- BOOKS SECTION ---
            b_tab = self.archive_tabs.tab("Archived Books")
            b_controls = ctk.CTkFrame(b_tab, fg_color="transparent", height=40)
            b_controls.pack(fill="x", padx=10, pady=(5, 0))

            self.sel_all_books_var = tk.IntVar(value=0)
            CTkCheckBox(b_controls, text="Select All", variable=self.sel_all_books_var,
                        command=self.toggle_archive_books, text_color="black").pack(side="left")

            self.lbl_arch_book_count = CTkLabel(b_controls, text="0 Selected", text_color="black")
            self.lbl_arch_book_count.pack(side="left", padx=10)

            self.btn_bulk_del_books = CTkButton(b_controls, text="DELETE SELECTED", state="disabled",
                                                fg_color="#C0392B", command=self.bulk_delete_books)
            self.btn_bulk_del_books.pack(side="right", padx=5)

            self.btn_bulk_rest_books = CTkButton(b_controls, text="RESTORE SELECTED", state="disabled",
                                                 fg_color="#27AE60", command=self.bulk_restore_books)
            self.btn_bulk_rest_books.pack(side="right", padx=5)

            # Scrollable Frame for Books
            self.book_archive_scroll = CTkScrollableFrame(b_tab, fg_color="ivory4", corner_radius=20)
            self.book_archive_scroll.pack(fill="both", expand=True, padx=10, pady=(10, 10))

            # --- STUDENTS SECTION ---
            s_tab = self.archive_tabs.tab("Archived Students")
            s_controls = ctk.CTkFrame(s_tab, fg_color="transparent", height=40)
            s_controls.pack(fill="x", padx=10, pady=(5, 0))
            self.sel_all_stud_var = tk.IntVar(value=0)
            CTkCheckBox(s_controls, text="Select All", variable=self.sel_all_stud_var,
                        command=self.toggle_archive_students, text_color="black").pack(side="left")
            self.lbl_arch_stud_count = CTkLabel(s_controls, text="0 Selected", text_color="black")
            self.lbl_arch_stud_count.pack(side="left", padx=10)
            self.btn_bulk_del_stud = CTkButton(s_controls, text="DELETE SELECTED", state="disabled", fg_color="#C0392B",
                                               command=self.bulk_delete_students)
            self.btn_bulk_del_stud.pack(side="right", padx=5)
            self.btn_bulk_rest_stud = CTkButton(s_controls, text="RESTORE SELECTED", state="disabled",
                                                fg_color="#27AE60", command=self.bulk_restore_students)
            self.btn_bulk_rest_stud.pack(side="right", padx=5)

            # Scrollable Frame for Students
            self.student_archive_scroll = CTkScrollableFrame(s_tab, fg_color="ivory4", corner_radius=20)
            self.student_archive_scroll.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        self.reload_book_archives()
        self.reload_student_archives()

    def reload_book_archives(self):
        for w in self.book_archive_scroll.winfo_children(): w.destroy()
        data = self.fetch_data("archived_books")

        self.archive_book_vars = {}
        self.archive_book_ids = {}
        self.sel_all_books_var.set(0)
        self.update_archive_book_counter()

        if not data:
            CTkLabel(self.book_archive_scroll, text="No Archived Books", text_color="black").pack(pady=20)
            return

        # --- HEADERS (Using Grid) ---
        headers = ["SEL", "ORIG ID", "TITLE", "AUTHOR", "AISLE", "CATEGORY", "DATE", "ACTION"]
        weights = [0, 0, 3, 2, 0, 1, 1, 0]
        min_widths = [30, 30, 0, 0, 50, 0, 0, 150]  # Increased action width for 2 buttons

        for c, h in enumerate(headers):
            self.book_archive_scroll.grid_columnconfigure(c, weight=weights[c])
            width_val = min_widths[c] if weights[c] == 0 else 0
            CTkLabel(self.book_archive_scroll, text=h, font=("Agency FB", 18, "bold"), text_color="black",
                     width=width_val, anchor="w").grid(row=0, column=c, padx=5, pady=10, sticky="ew")

        # --- DATA ROWS (Using Grid) ---
        for idx, row in enumerate(data):
            arch_id = row[8]  # ARCHIVE_ID

            var = tk.IntVar(value=0)
            CTkCheckBox(self.book_archive_scroll, text="", variable=var, width=20,
                        command=self.update_archive_book_counter).grid(row=idx + 1, column=0, padx=10, sticky="w")

            self.archive_book_vars[idx] = var
            self.archive_book_ids[idx] = arch_id

            # row data mapping: [ORIG, TITLE, AUTHOR, AISLE, DATE, PUB, CAT, ARCH_DATE, ARCH_ID]
            # Table cols: [SEL(0), ORIG(1), TITLE(2), AUTHOR(3), AISLE(4), CAT(5), DATE(6), ACTION(7)]
            val_map = {
                1: row[0],  # Orig ID
                2: row[1],  # Title
                3: row[2],  # Author
                4: row[3],  # Aisle
                5: row[6],  # Category
                6: row[7]  # Date
            }

            for col_idx, val_text in val_map.items():
                is_flexible = weights[col_idx] > 0
                wrap_val = 150 if is_flexible else 0
                CTkLabel(self.book_archive_scroll, text=str(val_text), font=("Agency FB", 18), text_color="black",
                         wraplength=wrap_val, anchor="w") \
                    .grid(row=idx + 1, column=col_idx, padx=5, pady=5, sticky="ew")

            # Actions (Grid inside Grid)
            btn_frame = ctk.CTkFrame(self.book_archive_scroll, fg_color="transparent")
            btn_frame.grid(row=idx + 1, column=7, padx=5, sticky="ew")

            CTkButton(btn_frame, text="RESTORE", width=70, height=25, fg_color="#27AE60",
                      command=lambda aid=arch_id: self.restore_book(aid)).pack(side="left", padx=2)
            CTkButton(btn_frame, text="DELETE", width=70, height=25, fg_color="#C0392B",
                      command=lambda aid=arch_id: self.delete_archived_book(aid)).pack(side="left", padx=2)

    def toggle_archive_books(self):
        state = self.sel_all_books_var.get()
        for v in self.archive_book_vars.values(): v.set(state)
        self.update_archive_book_counter()

    def update_archive_book_counter(self):
        count = sum(v.get() for v in self.archive_book_vars.values())
        self.lbl_arch_book_count.configure(text=f"{count} Selected")
        state = "normal" if count > 0 else "disabled"
        self.btn_bulk_del_books.configure(state=state)
        self.btn_bulk_rest_books.configure(state=state)

    def bulk_restore_books(self):
        ids = [self.archive_book_ids[k] for k, v in self.archive_book_vars.items() if v.get() == 1]
        if not ids: return
        if not messagebox.askyesno("Confirm", f"Restore {len(ids)} books?"): return
        try:
            for aid in ids:
                self.restore_book(aid, prompt=False)
            messagebox.showinfo("Success", "Books Restored.")
            self.refresh_archive_table()
            self.refresh_list_table()
        except Exception as e:
            messagebox.showerror("Error", f"Bulk restore failed: {e}")

    def bulk_delete_books(self):
        ids = [self.archive_book_ids[k] for k, v in self.archive_book_vars.items() if v.get() == 1]
        if not ids: return
        if not messagebox.askyesno("Confirm", f"Delete {len(ids)} books permanently?"): return
        try:
            for aid in ids:
                self.delete_archived_book(aid, prompt=False)
            messagebox.showinfo("Success", "Books Deleted.")
            self.refresh_archive_table()
        except Exception as e:
            messagebox.showerror("Error", f"Bulk delete failed: {e}")

    # ------------------ ARCHIVE STUDENT LOGIC ------------------ #
    def reload_student_archives(self):
        for w in self.student_archive_scroll.winfo_children(): w.destroy()
        data = self.fetch_data("archived_students")

        self.archive_student_vars = {}
        self.archive_student_ids = {}
        self.sel_all_stud_var.set(0)
        self.update_archive_student_counter()

        # Fixed Header using Grid for consistency
        headers = ["SEL", "STUDENT INFO", "ARCHIVED DATE", "ACTIONS"]
        col_weights = [0, 1, 1, 0]
        col_widths = [40, 0, 0, 150]

        for c, h in enumerate(headers):
            self.student_archive_scroll.grid_columnconfigure(c, weight=col_weights[c])
            width_val = col_widths[c] if col_weights[c] == 0 else 0
            CTkLabel(self.student_archive_scroll, text=h, font=("Arial", 12, "bold"), text_color="black",
                     width=width_val, anchor="w").grid(row=0, column=c, padx=5, pady=5, sticky="ew")

        if not data:
            CTkLabel(self.student_archive_scroll, text="No Archived Students", text_color="black").grid(row=1, column=0,
                                                                                                        columnspan=4,
                                                                                                        pady=20)
            return

        for idx, row in enumerate(data):
            arch_id = row[0]

            var = tk.IntVar(value=0)
            CTkCheckBox(self.student_archive_scroll, text="", variable=var, width=30,
                        command=self.update_archive_student_counter).grid(row=idx + 1, column=0, padx=5, sticky="w")

            self.archive_student_vars[idx] = var
            self.archive_student_ids[idx] = arch_id

            info = f"{row[2]} ({row[1]})"  # Name (Num)

            CTkLabel(self.student_archive_scroll, text=info, font=("Arial", 12), text_color="black", anchor="w") \
                .grid(row=idx + 1, column=1, padx=5, sticky="ew")

            CTkLabel(self.student_archive_scroll, text=str(row[3]), font=("Arial", 12), text_color="black", anchor="w") \
                .grid(row=idx + 1, column=2, padx=5, sticky="ew")

            btn_frame = ctk.CTkFrame(self.student_archive_scroll, fg_color="transparent")
            btn_frame.grid(row=idx + 1, column=3, padx=5, sticky="ew")

            CTkButton(btn_frame, text="RESTORE", width=70, height=25, fg_color="#27AE60",
                      command=lambda aid=arch_id: self.restore_student(aid)).pack(side="left", padx=2)

            CTkButton(btn_frame, text="DELETE", width=70, height=25, fg_color="#C0392B",
                      command=lambda aid=arch_id: self.delete_archived_student(aid)).pack(side="left", padx=5)

    def toggle_archive_students(self):
        state = self.sel_all_stud_var.get()
        for v in self.archive_student_vars.values(): v.set(state)
        self.update_archive_student_counter()

    def update_archive_student_counter(self):
        count = sum(v.get() for v in self.archive_student_vars.values())
        self.lbl_arch_stud_count.configure(text=f"{count} Selected")
        state = "normal" if count > 0 else "disabled"
        self.btn_bulk_del_stud.configure(state=state)
        self.btn_bulk_rest_stud.configure(state=state)

    def bulk_restore_students(self):
        ids = [self.archive_student_ids[k] for k, v in self.archive_student_vars.items() if v.get() == 1]
        if not ids: return
        if not messagebox.askyesno("Confirm", f"Restore {len(ids)} students?"): return
        try:
            for aid in ids:
                self.restore_student(aid, prompt=False)
            messagebox.showinfo("Success", "Students Restored.")
            self.refresh_archive_table()
            self.refresh_student_list()
        except Exception as e:
            messagebox.showerror("Error", f"Bulk restore failed: {e}")

    def bulk_delete_students(self):
        ids = [self.archive_student_ids[k] for k, v in self.archive_student_vars.items() if v.get() == 1]
        if not ids: return
        if not messagebox.askyesno("Confirm", f"Delete {len(ids)} students permanently?"): return
        try:
            for aid in ids:
                self.delete_archived_student(aid, prompt=False)
            messagebox.showinfo("Success", "Students Deleted.")
            self.refresh_archive_table()
        except Exception as e:
            messagebox.showerror("Error", f"Bulk delete failed: {e}")

    # ------------------ INDIVIDUAL RESTORE/DELETE ACTIONS ------------------ #
    def restore_book(self, archive_id, prompt=True):
        if not DB_CONNECTED: return
        if prompt:
            confirm = messagebox.askyesno("Confirm Restore", "Restore this book to the active list?")
            if not confirm: return
        try:
            # UPDATED: Copy all columns including AISLE
            restore_query = """
            INSERT INTO books (BOOKID, TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY)
            SELECT ORIGINAL_ID, TITLE, AUTHOR, AISLE, PUBLISHED_DATE, PUBLISHER, CATEGORY FROM archived_books WHERE ARCHIVE_ID = %s
            """
            myCursor.execute(restore_query, (archive_id,))

            del_query = "DELETE FROM archived_books WHERE ARCHIVE_ID = %s"
            myCursor.execute(del_query, (archive_id,))

            myDB.commit()
            if prompt:
                messagebox.showinfo("Success", "Book Restored successfully.")
                self.refresh_archive_table()
                self.refresh_list_table()
        except Exception as e:
            myDB.rollback()
            if prompt: messagebox.showerror("Error", f"Failed to restore (ID might already exist): {e}")
            raise e

    def delete_archived_book(self, archive_id, prompt=True):
        if not DB_CONNECTED: return
        if prompt:
            confirm = messagebox.askyesno("Confirm Delete", "Permanently delete this book?\nThis cannot be undone.")
            if not confirm: return

        try:
            query = "DELETE FROM archived_books WHERE ARCHIVE_ID = %s"
            myCursor.execute(query, (archive_id,))
            myDB.commit()
            if prompt:
                messagebox.showinfo("Deleted", "Book Permanently Deleted.")
                self.refresh_archive_table()
        except Exception as e:
            myDB.rollback()
            if prompt: messagebox.showerror("Error", f"Delete Failed: {e}")
            raise e

    def restore_student(self, archive_id, prompt=True):
        if not DB_CONNECTED: return
        if prompt:
            if not messagebox.askyesno("Confirm", "Restore this student?"): return
        try:
            res_query = """
            INSERT INTO students (STUDENT_NUMBER, NAME)
            SELECT ORIGINAL_STUDENT_NUMBER, NAME FROM archived_students WHERE ARCHIVE_ID = %s
            """
            myCursor.execute(res_query, (archive_id,))

            del_query = "DELETE FROM archived_students WHERE ARCHIVE_ID = %s"
            myCursor.execute(del_query, (archive_id,))

            myDB.commit()
            if prompt:
                messagebox.showinfo("Success", "Student Restored Successfully!")
                self.refresh_archive_table()
                self.refresh_student_list()

        except Exception as e:
            myDB.rollback()
            if prompt: messagebox.showerror("Error", f"Restore Failed: {e}")
            raise e

    def delete_archived_student(self, archive_id, prompt=True):
        if not DB_CONNECTED: return
        if prompt:
            confirm = messagebox.askyesno("Confirm Delete", "Permanently delete this record?\nThis cannot be undone.")
            if not confirm: return

        try:
            query = "DELETE FROM archived_students WHERE ARCHIVE_ID = %s"
            myCursor.execute(query, (archive_id,))
            myDB.commit()
            if prompt:
                messagebox.showinfo("Deleted", "Record Permanently Deleted.")
                self.refresh_archive_table()
        except Exception as e:
            myDB.rollback()
            if prompt: messagebox.showerror("Error", f"Delete Failed: {e}")
            raise e

    # __________________ CURIO (TRIVIA/ANNOUNCEMENTS) __________________ #
    def drawBorrowTab(self) -> None:
        tab_frame = self.bookTabs.tab("Borrow")
        tab_frame.configure(fg_color="transparent")
        if len(tab_frame.winfo_children()) > 0: return

        curio_container = ctk.CTkFrame(master=tab_frame, fg_color="transparent")
        curio_container.pack(fill="both", expand=True, padx=20, pady=20)

        left_frame = ctk.CTkFrame(curio_container, fg_color="transparent", width=400)
        left_frame.pack(side="left", fill="y", padx=(0, 20), expand=False)
        CTkLabel(left_frame, text="Add New Curios", font=("Agency FB", 24), text_color="white").pack(anchor="w",
                                                                                                     pady=(0, 10))

        self.entry_curio_title = CTkEntry(left_frame, fg_color=self.SIDEBAR_COLOR, text_color="white")
        self.entry_curio_title.pack(fill="x", pady=(0, 10))
        self.combo_curio_type = CTkComboBox(left_frame, values=["Trivia", "Announcement", "Event"],
                                            fg_color=self.SIDEBAR_COLOR)
        self.combo_curio_type.pack(fill="x", pady=(0, 10))

        self.text_curio_content = CTkTextbox(left_frame, fg_color=self.SIDEBAR_COLOR, text_color="white", height=100,
                                             wrap="word")
        self.text_curio_content.pack(fill="x", pady=(0, 10))

        self.entry_curio_answer = CTkEntry(left_frame, fg_color=self.SIDEBAR_COLOR, text_color="white",
                                           placeholder_text="Answer (if trivia)")
        self.entry_curio_answer.pack(fill="x", pady=(0, 20))

        self.btn_curio_upload = CTkButton(left_frame, text="Upload", command=self.save_curio_action, fg_color="#D9F9D4",
                                          text_color="black")
        self.btn_curio_upload.pack(fill="x")

        right_frame = ctk.CTkFrame(curio_container, fg_color="#8FBC8F", corner_radius=15)
        right_frame.pack(side="right", fill="both", expand=True)
        CTkLabel(right_frame, text="Current Curios (From DB)", font=("Agency FB", 24), text_color="white").pack(
            anchor="nw",
            padx=20, pady=20)

        self.curio_list_scroll = CTkScrollableFrame(right_frame, fg_color="transparent")
        self.curio_list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.refresh_curio_list()

    def refresh_curio_list(self) -> None:
        for w in self.curio_list_scroll.winfo_children(): w.destroy()
        data = self.fetch_data("curio_list")
        self.curio_db_map = {}
        if not data:
            CTkLabel(self.curio_list_scroll, text="No items found.", text_color="gray").pack(pady=10)
            return
        for i, row in enumerate(data):
            c_id, title, c_type = row[0], row[1], row[2]
            self.curio_db_map[i] = row
            CTkLabel(self.curio_list_scroll, text=f"{title} ({c_type})", text_color="white",
                     font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="w", padx=10, pady=2)
            CTkButton(self.curio_list_scroll, text="Edit", width=60, height=25,
                      command=lambda idx=i: self.load_curio_edit(idx)).grid(row=i, column=1, padx=10, pady=2)

    def load_curio_edit(self, idx):
        if idx not in self.curio_db_map: return
        row = self.curio_db_map[idx]
        self.editing_curio_id = row[0]
        self.entry_curio_title.delete(0, 'end')
        self.entry_curio_title.insert(0, row[1])
        self.combo_curio_type.set(row[2])
        self.text_curio_content.delete("0.0", 'end')
        self.text_curio_content.insert("0.0", row[5])
        self.entry_curio_answer.delete(0, 'end')
        if row[6]: self.entry_curio_answer.insert(0, row[6])
        self.btn_curio_upload.configure(text="Update Item", fg_color="orange")

    def save_curio_action(self):
        if not DB_CONNECTED: return
        title = self.entry_curio_title.get()
        c_type = self.combo_curio_type.get()
        content = self.text_curio_content.get("0.0", "end").strip()
        answer = self.entry_curio_answer.get()
        today_date = date.today()
        if not title: messagebox.showwarning("Missing Info", "Title is required."); return

        try:
            if self.editing_curio_id is not None:
                query = "UPDATE curio SET TITLE=%s, TYPE=%s, CONTENT=%s, ANSWER=%s WHERE CURIO_ID=%s"
                vals = (title, c_type, content, answer, self.editing_curio_id)
                myCursor.execute(query, vals)
                messagebox.showinfo("Success", "Item Updated.")
            else:
                query = "INSERT INTO curio (TITLE, TYPE, PUBLISHED_DATE, VISIBILITY, CONTENT, ANSWER) VALUES (%s, %s, %s, %s, %s, %s)"
                vals = (title, c_type, today_date, "Public", content, answer)
                myCursor.execute(query, vals)
                messagebox.showinfo("Success", "Item Added.")
            myDB.commit()
            self.entry_curio_title.delete(0, 'end')
            self.text_curio_content.delete("0.0", 'end')
            self.entry_curio_answer.delete(0, 'end')
            self.editing_curio_id = None
            self.btn_curio_upload.configure(text="Upload", fg_color="#D9F9D4")
            self.refresh_curio_list()
        except Exception as e:
            myDB.rollback()
            messagebox.showerror("Error", f"Database Error: {e}")

    # __________________ RECORDS / HISTORY LOGIC __________________ #
    def check_attendance_suggestions(self, event) -> None:
        typed_text = self.att_search_entry.get().lower()
        if not typed_text:
            try:
                self.att_suggestion_frame.place_forget()
            except:
                pass
            return

        all_students = self.fetch_data("records")
        matches = []
        for s in all_students:
            if typed_text in s[2].lower() or typed_text in str(s[1]).lower():
                matches.append(f"{s[2]} | {s[1]}")

        self.update_att_suggestion_box(matches)

    def update_att_suggestion_box(self, matches: List[str]) -> None:
        if not hasattr(self, 'att_suggestion_frame'): return
        for widget in self.att_suggestion_frame.winfo_children(): widget.destroy()
        if not matches:
            self.att_suggestion_frame.place_forget()
            return

        self.att_suggestion_frame.place(relx=0.5, y=145, anchor="n")
        self.att_suggestion_frame.lift()

        for item in matches:
            CTkButton(self.att_suggestion_frame, text=item, font=("Arial", 14), anchor="w",
                      fg_color="transparent", text_color="black", hover_color="#E0E0E0", height=30,
                      command=lambda v=item: self.select_att_suggestion(v)).pack(fill="x", padx=5, pady=2)

    def select_att_suggestion(self, value: str) -> None:
        self.att_search_entry.delete(0, "end")
        self.att_search_entry.insert(0, value.split(" | ")[0])
        self.att_suggestion_frame.place_forget()

        student_num = value.split(" | ")[1]
        self.perform_attendance_action(student_num)

    def perform_attendance_action(self, student_identifier: str):
        if not DB_CONNECTED: return

        try:
            query = "SELECT ID, NAME FROM students WHERE STUDENT_NUMBER = %s OR NAME = %s"
            myCursor.execute(query, (student_identifier, student_identifier))
            res = myCursor.fetchone()

            if not res:
                messagebox.showerror("Error", "Student not found.")
                return

            student_id = res[0]
            student_name = res[1]

            check_sql = "SELECT LOG_ID FROM attendance_logs WHERE STUDENT_ID = %s AND TIME_OUT IS NULL"
            myCursor.execute(check_sql, (student_id,))
            active_log = myCursor.fetchone()

            if active_log:
                log_id = active_log[0]
                upd_sql = "UPDATE attendance_logs SET TIME_OUT = NOW() WHERE LOG_ID = %s"
                myCursor.execute(upd_sql, (log_id,))
                msg = f"GOODBYE! {student_name} has Timed OUT."
            else:
                ins_sql = "INSERT INTO attendance_logs (STUDENT_ID, TIME_IN) VALUES (%s, NOW())"
                myCursor.execute(ins_sql, (student_id,))
                msg = f"WELCOME! {student_name} has Timed IN."

            myDB.commit()
            messagebox.showinfo("Attendance", msg)
            self.att_search_entry.delete(0, 'end')
            self.refresh_attendance_table()

        except Exception as e:
            myDB.rollback()
            messagebox.showerror("Error", f"Action failed: {e}")

    def fetch_attendance_by_date(self, target_date):
        if not DB_CONNECTED: return []
        query = """
        SELECT s.NAME, s.STUDENT_NUMBER, a.TIME_IN, a.TIME_OUT, a.LOG_ID, a.STUDENT_ID
        FROM attendance_logs a
        JOIN students s ON a.STUDENT_ID = s.ID
        WHERE DATE(a.TIME_IN) = %s
        ORDER BY a.TIME_IN DESC
        """
        try:
            myCursor.execute(query, (target_date,))
            return myCursor.fetchall()
        except Exception as e:
            print(e)
            return []

    def manual_time_out(self, log_id):
        if not DB_CONNECTED: return
        try:
            upd_sql = "UPDATE attendance_logs SET TIME_OUT = NOW() WHERE LOG_ID = %s"
            myCursor.execute(upd_sql, (log_id,))
            myDB.commit()
            self.refresh_attendance_table()
        except Exception as e:
            myDB.rollback()
            print(e)

    def drawHistoryTab(self) -> None:
        tab = self.bookTabs.tab("History")
        tab.configure(fg_color="transparent")
        if len(tab.winfo_children()) > 0: return

        self.left_att_frame = ctk.CTkFrame(tab, fg_color=self.CONTENT_BG_COLOR, corner_radius=15)
        self.left_att_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=10)

        self.right_man_frame = ctk.CTkFrame(tab, fg_color="#F0F0F0", corner_radius=15)
        self.right_man_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=10)

        # ---------------- LEFT SIDE (ATTENDANCE) ---------------- #
        CTkLabel(self.left_att_frame, text="DAILY ATTENDANCE", font=("Agency FB", 28, "bold"),
                 text_color=self.SIDEBAR_COLOR).pack(pady=(20, 10))

        # --- CALENDAR SELECTION ---
        date_frame = ctk.CTkFrame(self.left_att_frame, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=5)

        CTkLabel(date_frame, text="Select Date:", text_color="black", font=("Arial", 12, "bold")).pack(side="left")

        # 1. Calendar Widget (DateEntry)
        self.cal_att_date = DateEntry(
            date_frame,
            width=12,
            background='#30443B',  # Dark Sidebar Color (Header BG)
            foreground='white',  # Header Text Color
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            headersbackground='#4F7942',  # Medium Green
            headersforeground='white',  # Day names Text
            selectbackground='#2E8B57',  # Selection Highlight
            selectforeground='white',  # Selection Text
            normalbackground='#D9F9D4',  # Normal days BG
            normalforeground='black',  # Normal days Text
            weekendbackground='#C1E1C1',  # Weekends BG
            weekendforeground='black'  # Weekends Text
        )
        self.cal_att_date.pack(side="left", padx=10)
        self.cal_att_date.bind("<<DateEntrySelected>>", lambda e: self.refresh_attendance_table())

        # 2. TODAY Button
        CTkButton(date_frame, text="TODAY", width=60, fg_color="#27AE60",
                  command=self.set_date_today).pack(side="left", padx=5)

        # 3. Refresh Button
        CTkButton(date_frame, text="REFRESH", width=60, fg_color=self.SIDEBAR_COLOR,
                  command=self.refresh_attendance_table).pack(side="left", padx=5)

        # --- SEARCH BAR ---
        search_cont = ctk.CTkFrame(self.left_att_frame, fg_color="white", corner_radius=10, height=40)
        search_cont.pack(fill="x", padx=20, pady=(10, 20))
        search_cont.pack_propagate(False)

        self.att_search_entry = CTkEntry(search_cont, placeholder_text="Search Student Name to Time In/Out...",
                                         border_width=0, fg_color="transparent", text_color="black")
        self.att_search_entry.pack(fill="both", expand=True, padx=10, pady=5)
        self.att_search_entry.bind("<KeyRelease>", self.check_attendance_suggestions)

        self.att_suggestion_frame = CTkScrollableFrame(self.left_att_frame, width=300, height=120, fg_color="white",
                                                       corner_radius=10, border_width=1, border_color="gray")

        # --- TABLE HEADERS ---
        headers = ["NAME", "TIME IN", "TIME OUT"]
        h_frame = ctk.CTkFrame(self.left_att_frame, fg_color="transparent")
        h_frame.pack(fill="x", padx=20)
        for h in headers:
            CTkLabel(h_frame, text=h, font=("Arial", 12, "bold"), text_color="black", width=120, anchor="w").pack(
                side="left", padx=5, expand=True)

        self.attendance_scroll = CTkScrollableFrame(self.left_att_frame, fg_color="white", corner_radius=10)
        self.attendance_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Load initial data
        self.refresh_attendance_table()

        # ---------------- RIGHT SIDE (MANAGE STUDENTS) ---------------- #
        CTkLabel(self.right_man_frame, text="MANAGE STUDENTS", font=("Agency FB", 28, "bold"), text_color="black").pack(
            pady=(20, 10))

        form_frame = ctk.CTkFrame(self.right_man_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=20)

        self.entry_student_num = CTkEntry(form_frame, placeholder_text="Student Number")
        self.entry_student_num.pack(fill="x", pady=5)

        self.entry_student_name = CTkEntry(form_frame, placeholder_text="Student Name")
        self.entry_student_name.pack(fill="x", pady=5)

        self.btn_student_save = CTkButton(form_frame, text="ADD STUDENT", fg_color=self.MAIN_BG_COLOR,
                                          command=self.save_student_action)
        self.btn_student_save.pack(fill="x", pady=10)
        CTkButton(form_frame, text="CLEAR", fg_color="gray", height=20, command=self.clear_student_form).pack(fill="x")

        CTkLabel(self.right_man_frame, text="ALL REGISTERED STUDENTS", font=("Arial", 14, "bold"),
                 text_color="gray").pack(pady=(20, 5))

        self.student_list_scroll = CTkScrollableFrame(self.right_man_frame, fg_color="white")
        self.student_list_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_student_list()

    def set_date_today(self):
        self.cal_att_date.set_date(date.today())
        self.refresh_attendance_table()

    def refresh_attendance_table(self):
        # Clear
        for w in self.attendance_scroll.winfo_children(): w.destroy()

        # Get date from Calendar Widget
        target_date = self.cal_att_date.get_date()
        data = self.fetch_attendance_by_date(target_date)

        if not data:
            CTkLabel(self.attendance_scroll, text=f"No records for {target_date}", text_color="gray").pack(pady=20)
            return

        for row in data:
            name = row[0]
            t_in = row[2].strftime("%I:%M %p") if row[2] else "--"

            row_frame = ctk.CTkFrame(self.attendance_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            CTkLabel(row_frame, text=name, text_color="black", width=120, anchor="w").pack(side="left", padx=5,
                                                                                           expand=True)
            CTkLabel(row_frame, text=t_in, text_color="green", width=120, anchor="w").pack(side="left", padx=5,
                                                                                           expand=True)

            if row[3]:
                t_out = row[3].strftime("%I:%M %p")
                CTkLabel(row_frame, text=t_out, text_color="red", width=120, anchor="w").pack(side="left", padx=5,
                                                                                              expand=True)
            else:
                if str(target_date) == str(date.today()):
                    CTkButton(row_frame, text="TIME OUT", fg_color="#C0392B", width=80, height=20,
                              command=lambda lid=row[4]: self.manual_time_out(lid)).pack(side="left", padx=5,
                                                                                         expand=True)
                else:
                    CTkLabel(row_frame, text="--", text_color="gray").pack(side="left", expand=True)

    def refresh_student_list(self):
        """
        a function that refreshes the student list when any changes are made
        :return:
        """
        for w in self.student_list_scroll.winfo_children(): w.destroy()

        data = self.fetch_data("records")
        if not data: return

        for row in data:
            row_frame = ctk.CTkFrame(self.student_list_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            CTkLabel(row_frame, text=f"{row[2]}\n({row[1]})", font=("Arial", 12), text_color="black", anchor="w").pack(
                side="left", padx=5, expand=True)

            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.pack(side="right")

            CTkButton(btn_frame, text="Edit", width=40, height=20, fg_color="orange",
                      command=lambda r=row: self.load_student_edit(r)).pack(side="left", padx=2)
            CTkButton(btn_frame, text="Arc", width=40, height=20, fg_color="red",
                      command=lambda r=row: self.archive_student(r)).pack(side="left", padx=2)

    def load_student_edit(self, row):
        """
        a function that loads in a student's info the the edit entry
        :param row:
        :return:
        """
        self.student_edit_id = row[0]
        self.entry_student_num.delete(0, 'end')
        self.entry_student_num.insert(0, row[1])
        self.entry_student_name.delete(0, 'end')
        self.entry_student_name.insert(0, row[2])
        self.btn_student_save.configure(text="UPDATE STUDENT")

    def clear_student_form(self):
        """
        clear's the student info from the entries
        :return:
        """
        self.student_edit_id = None
        self.entry_student_num.delete(0, 'end')
        self.entry_student_name.delete(0, 'end')
        self.btn_student_save.configure(text="ADD STUDENT")

    def save_student_action(self):
        """
        saves a student record onto the database
        :return:
        """
        if not DB_CONNECTED: return

        s_num = self.entry_student_num.get().strip()
        s_name = self.entry_student_name.get().strip()

        if not s_num or not s_name:
            messagebox.showwarning("Error", "Student Number and Name are required.")
            return

        try:
            if self.student_edit_id:
                check_query = "SELECT COUNT(*) FROM students WHERE STUDENT_NUMBER = %s AND ID != %s"
                myCursor.execute(check_query, (s_num, self.student_edit_id))
                if myCursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "Student Number already exists!")
                    return

                query = "UPDATE students SET STUDENT_NUMBER=%s, NAME=%s WHERE ID=%s"
                myCursor.execute(query, (s_num, s_name, self.student_edit_id))
                messagebox.showinfo("Success", "Student Updated.")

            else:
                check_query = "SELECT COUNT(*) FROM students WHERE STUDENT_NUMBER = %s"
                myCursor.execute(check_query, (s_num,))
                if myCursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "Student Number is already used!")
                    return

                query = "INSERT INTO students (STUDENT_NUMBER, NAME) VALUES (%s, %s)"
                myCursor.execute(query, (s_num, s_name))
                messagebox.showinfo("Success", "Student Added.")

            myDB.commit()
            self.clear_student_form()
            self.refresh_student_list()

        except Exception as e:
            myDB.rollback()
            messagebox.showerror("Error", f"Database Error: {e}")

    def archive_student(self, row):
        """
        a function that archives the student by copying it to another table and deleting itself
        :param row:
        :return:
        """
        if not DB_CONNECTED: return

        confirm = messagebox.askyesno("Archive", f"Archive student {row[1]}?")
        if not confirm: return

        try:
            copy_sql = "INSERT INTO archived_students (ORIGINAL_STUDENT_NUMBER, NAME) VALUES (%s, %s)"
            myCursor.execute(copy_sql, (row[1], row[2]))

            del_sql = "DELETE FROM students WHERE ID = %s"
            myCursor.execute(del_sql, (row[0],))

            myDB.commit()
            messagebox.showinfo("Success", "Student Archived.")
            self.refresh_student_list()

        except Exception as e:
            myDB.rollback()
            messagebox.showerror("Error", f"Archive Failed: {e}")

    def placeObjects(self) -> None:
        """
        places the application's objects
        :return:
        """
        self.drawDashboard()
        self.listBooks()
        self.drawBorrowTab()
        self.drawHistoryTab()
        self.changeTab("HOME")
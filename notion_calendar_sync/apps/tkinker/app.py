import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import date

from notion_calendar_sync.local.updater import Calendar
from notion_calendar_sync.local.builder import build_calendar


class CalendarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calendar App")
        self.cal = Calendar()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Add Event tab
        self.event_tab = ttk.Frame(notebook)
        notebook.add(self.event_tab, text="Add Event")
        self._build_event_tab()

        # Add Task tab
        self.task_tab = ttk.Frame(notebook)
        notebook.add(self.task_tab, text="Add Task")
        self._build_task_tab()

        # Build tab
        self.build_tab = ttk.Frame(notebook)
        notebook.add(self.build_tab, text="Preview/Build")
        self._build_build_tab()

    def _build_event_tab(self):
        labels = [
            "Title",
            "Event Type",
            "Location",
            "Room",
            "Date (YYYY-MM-DD)",
            "Start (HH:MM)",
            "End (HH:MM)",
            "Repeat (comma dates)",
        ]
        self.event_entries = {}
        for i, lab in enumerate(labels):
            ttk.Label(self.event_tab, text=lab).grid(row=i, column=0, sticky="e")
            entry = ttk.Entry(self.event_tab, width=30)
            entry.grid(row=i, column=1)
            self.event_entries[lab] = entry
        ttk.Button(self.event_tab, text="Save", command=self.save_event).grid(
            row=len(labels), column=0, columnspan=2, pady=5
        )

    def save_event(self):
        e = self.event_entries
        repeat = [
            d.strip() for d in e["Repeat (comma dates)"].get().split(",") if d.strip()
        ]
        try:
            self.cal.add_event(
                event=e["Title"].get(),
                eventtype=e["Event Type"].get(),
                location=e["Location"].get(),
                room=e["Room"].get() or None,
                date=e["Date (YYYY-MM-DD)"].get(),
                start=e["Start (HH:MM)"].get(),
                end=e["End (HH:MM)"].get(),
                repeat=repeat or None,
            )
            messagebox.showinfo("Saved", "Event saved")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _build_task_tab(self):
        labels = ["Task", "Due Date (YYYY-MM-DD)", "Priority", "Notes"]
        self.task_entries = {}
        for i, lab in enumerate(labels):
            ttk.Label(self.task_tab, text=lab).grid(row=i, column=0, sticky="e")
            entry = ttk.Entry(self.task_tab, width=30)
            entry.grid(row=i, column=1)
            self.task_entries[lab] = entry
        self.task_entries["Priority"].insert(0, "medium")
        ttk.Button(self.task_tab, text="Save", command=self.save_task).grid(
            row=len(labels), column=0, columnspan=2, pady=5
        )

    def save_task(self):
        t = self.task_entries
        try:
            self.cal.add_task(
                task=t["Task"].get(),
                due_date=t["Due Date (YYYY-MM-DD)"].get(),
                priority=t["Priority"].get(),
                notes=t["Notes"].get(),
            )
            messagebox.showinfo("Saved", "Task saved")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _build_build_tab(self):
        self.events_path_var = tk.StringVar(value="calendar.json")
        ttk.Label(self.build_tab, text="Events JSONL").grid(row=0, column=0, sticky="e")
        ttk.Entry(self.build_tab, textvariable=self.events_path_var, width=30).grid(
            row=0, column=1
        )
        ttk.Button(self.build_tab, text="Browse", command=self._browse).grid(
            row=0, column=2
        )

        self.view_var = tk.StringVar(value="monthly")
        ttk.Label(self.build_tab, text="View").grid(row=1, column=0, sticky="e")
        ttk.Combobox(
            self.build_tab, textvariable=self.view_var, values=["monthly", "weekly"]
        ).grid(row=1, column=1)

        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.week_var = tk.StringVar()
        ttk.Label(self.build_tab, text="Year").grid(row=2, column=0, sticky="e")
        ttk.Entry(self.build_tab, textvariable=self.year_var, width=10).grid(
            row=2, column=1, sticky="w"
        )
        ttk.Label(self.build_tab, text="Month").grid(row=3, column=0, sticky="e")
        ttk.Entry(self.build_tab, textvariable=self.month_var, width=10).grid(
            row=3, column=1, sticky="w"
        )
        ttk.Label(self.build_tab, text="Week date").grid(row=4, column=0, sticky="e")
        ttk.Entry(self.build_tab, textvariable=self.week_var, width=10).grid(
            row=4, column=1, sticky="w"
        )

        self.include_tasks_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.build_tab, text="Include Tasks", variable=self.include_tasks_var
        ).grid(row=5, column=0, columnspan=2)

        self.formats_var = {"pdf": tk.BooleanVar(value=True), "docx": tk.BooleanVar()}
        ttk.Checkbutton(
            self.build_tab, text="PDF", variable=self.formats_var["pdf"]
        ).grid(row=6, column=0)
        ttk.Checkbutton(
            self.build_tab, text="DOCX", variable=self.formats_var["docx"]
        ).grid(row=6, column=1)

        ttk.Button(self.build_tab, text="Build", command=self.build).grid(
            row=7, column=0, columnspan=2, pady=5
        )
        self.output_label = ttk.Label(self.build_tab, text="")
        self.output_label.grid(row=8, column=0, columnspan=3)

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.events_path_var.set(path)

    def build(self):
        formats = [fmt for fmt, var in self.formats_var.items() if var.get()]
        week_date = None
        if self.week_var.get():
            try:
                week_date = date.fromisoformat(self.week_var.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid week date")
                return
        try:
            outputs = build_calendar(
                events_path=Path(self.events_path_var.get()),
                view=self.view_var.get(),
                year=int(self.year_var.get()) if self.year_var.get() else None,
                month=int(self.month_var.get()) if self.month_var.get() else None,
                week=week_date,
                include_tasks=self.include_tasks_var.get(),
                formats=formats,
            )
            self.output_label.config(
                text="Generated: " + ", ".join(str(o) for o in outputs)
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


if __name__ == "__main__":
    app = CalendarApp()
    app.mainloop()

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import psutil
except ImportError:
    psutil = None

BG = "#0b0b12"
SIDEBAR = "#11111c"
PANEL = "#151522"
PANEL_HI = "#1b1b2b"
PURPLE = "#9b6bff"
PURPLE_DARK = "#33244f"
FG = "#f4f1ff"
MUTED = "#9793ad"
GREEN = "#54d6a0"
ORANGE = "#ffbd69"
RED = "#ff7185"
BORDER = "#29283a"


class PandaOptimizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panda PC Optimizer")
        self.geometry("1180x760")
        self.minsize(940, 650)
        self.configure(bg=BG)
        self.mode = tk.BooleanVar(value=False)
        self.search = tk.StringVar()
        self.status = tk.StringVar(value="Starting system monitor…")
        self.stats = {}
        self._rows = []
        self._after_id = None

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, foreground=FG,
                        fieldbackground=PANEL, rowheight=30, borderwidth=0,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=PANEL_HI, foreground=MUTED,
                        relief="flat", font=("Segoe UI", 9, "bold"), padding=(8, 9))
        style.map("Treeview", background=[("selected", PURPLE_DARK)],
                  foreground=[("selected", FG)])
        style.configure("Vertical.TScrollbar", background=PANEL, troughcolor=PANEL,
                        bordercolor=PANEL, arrowcolor=MUTED)

        self.build()
        self.refresh()
        self.schedule_tick()

    def label(self, parent, text, size=10, color=FG, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", parent.cget("bg")),
                        fg=color, font=("Segoe UI", size, "bold" if bold else "normal"),
                        **kwargs)

    def button(self, parent, text, cmd, primary=False, compact=False):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=PURPLE if primary else PANEL_HI, fg=FG,
            activebackground="#8050db", activeforeground="white",
            relief="flat", bd=0, padx=11 if compact else 14,
            pady=7 if compact else 10, cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            highlightthickness=0
        )

    def panel(self, parent, **kwargs):
        return tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                        highlightthickness=1, **kwargs)

    def build(self):
        shell = tk.Frame(self, bg=BG)
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg=SIDEBAR, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=19, pady=(23, 26))
        mark = tk.Label(brand, text="🐼", bg=PURPLE_DARK, fg=FG,
                        font=("Segoe UI Emoji", 20), width=2, height=1)
        mark.pack(side="left", padx=(0, 10))
        brand_text = tk.Frame(brand, bg=SIDEBAR)
        brand_text.pack(side="left")
        self.label(brand_text, "PANDA", 13, FG, True).pack(anchor="w")
        self.label(brand_text, "PC OPTIMIZER", 8, PURPLE, True).pack(anchor="w", pady=(1, 0))

        self.label(sidebar, "WORKSPACE", 8, MUTED, True).pack(anchor="w", padx=20, pady=(0, 9))
        self.nav_button(sidebar, "◈   Overview", True)
        self.nav_button(sidebar, "▤   Processes", False, lambda: self.focus_processes())
        self.nav_button(sidebar, "⚙   Windows tools", False, lambda: self.open_uri("ms-settings:"))
        self.nav_button(sidebar, "♡   Performance tips", False, lambda: self.show_tips())

        spacer = tk.Frame(sidebar, bg=SIDEBAR)
        spacer.pack(fill="both", expand=True)
        self.panel(sidebar, padx=12, pady=12).pack_forget()
        mode_card = tk.Frame(sidebar, bg="#1a1728", highlightbackground="#3a2c55", highlightthickness=1)
        mode_card.pack(fill="x", padx=13, pady=(0, 12))
        self.label(mode_card, "GAME MODE", 9, PURPLE, True).pack(anchor="w", padx=12, pady=(12, 4))
        self.label(mode_card, "Reduce monitor refreshes\nwhile you play.", 9, MUTED,
                   justify="left").pack(anchor="w", padx=12)
        tk.Checkbutton(mode_card, text="Enable Game Mode", variable=self.mode,
                       command=self.toggle_mode, bg="#1a1728", fg=FG,
                       selectcolor=PANEL_HI, activebackground="#1a1728",
                       activeforeground=FG, font=("Segoe UI", 9),
                       cursor="hand2").pack(anchor="w", padx=8, pady=(6, 11))
        self.label(sidebar, "LOCAL ONLY  •  NO TELEMETRY", 7, MUTED).pack(anchor="w", padx=18, pady=(0, 17))

        main = tk.Frame(shell, bg=BG)
        main.pack(side="left", fill="both", expand=True, padx=24, pady=21)

        top = tk.Frame(main, bg=BG)
        top.pack(fill="x", pady=(0, 19))
        left_top = tk.Frame(top, bg=BG)
        left_top.pack(side="left", fill="x", expand=True)
        self.label(left_top, "System overview", 23, FG, True).pack(anchor="w")
        self.label(left_top, "A clear picture of what your PC is doing right now.", 10, MUTED).pack(anchor="w", pady=(4, 0))
        self.button(top, "↻  Refresh now", self.refresh, primary=True).pack(side="right", anchor="center")

        self.status_pill = tk.Label(top, text="● MONITORING", bg="#14251f", fg=GREEN,
                                    padx=10, pady=6, font=("Segoe UI", 8, "bold"))
        self.status_pill.pack(side="right", padx=(0, 10), anchor="center")

        cards = tk.Frame(main, bg=BG)
        cards.pack(fill="x", pady=(0, 17))
        self.make_stat_card(cards, "cpu", "PROCESSOR", "CPU load", "Live usage across your CPU", PURPLE)
        self.make_stat_card(cards, "ram", "MEMORY", "RAM in use", "Used system memory", GREEN)
        self.make_stat_card(cards, "disk", "STORAGE", "System drive", "Space used on Windows drive", ORANGE)

        mid = tk.Frame(main, bg=BG)
        mid.pack(fill="both", expand=True)
        process_panel = self.panel(mid, padx=15, pady=14)
        process_panel.pack(side="left", fill="both", expand=True, padx=(0, 14))
        header = tk.Frame(process_panel, bg=PANEL)
        header.pack(fill="x", pady=(0, 10))
        titles = tk.Frame(header, bg=PANEL)
        titles.pack(side="left", fill="x", expand=True)
        self.label(titles, "Top resource users", 13, FG, True).pack(anchor="w")
        self.label(titles, "Processes sorted by current CPU activity", 9, MUTED).pack(anchor="w", pady=(3, 0))
        self.search_entry = tk.Entry(header, textvariable=self.search, bg=PANEL_HI, fg=FG,
                                     insertbackground=FG, relief="flat", font=("Segoe UI", 9),
                                     width=19)
        self.search_entry.pack(side="right", padx=(8, 0), ipady=7)
        self.search_entry.insert(0, "")
        self.search.trace_add("write", lambda *_: self.render_processes())

        table_wrap = tk.Frame(process_panel, bg=PANEL)
        table_wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_wrap, columns=("name", "cpu", "ram", "pid"),
                                 show="headings", selectmode="browse")
        for col, title, width in [
            ("name", "PROCESS", 230), ("cpu", "CPU %", 70),
            ("ram", "MEMORY MB", 95), ("pid", "PID", 65)
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w" if col == "name" else "center",
                             stretch=(col == "name"))
        scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        actions = tk.Frame(process_panel, bg=PANEL)
        actions.pack(fill="x", pady=(12, 0))
        self.label(actions, "Be careful: ending a task can lose unsaved work.", 8, MUTED).pack(side="left")
        self.button(actions, "End task…", self.end_task, compact=True).pack(side="right")

        right = tk.Frame(mid, bg=BG, width=238)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        health = self.panel(right, padx=14, pady=14)
        health.pack(fill="x", pady=(0, 13))
        self.label(health, "PC snapshot", 13, FG, True).pack(anchor="w")
        self.label(health, "Live system indicators", 9, MUTED).pack(anchor="w", pady=(3, 12))
        self.health_rows = {}
        for key, title in [("cpu", "Processor"), ("ram", "Memory"), ("disk", "Storage")]:
            line = tk.Frame(health, bg=PANEL)
            line.pack(fill="x", pady=5)
            row = tk.Frame(line, bg=PANEL)
            row.pack(fill="x")
            self.label(row, title, 9, MUTED).pack(side="left")
            val = self.label(row, "—", 9, FG, True)
            val.pack(side="right")
            bar_bg = tk.Frame(line, bg=PANEL_HI, height=5)
            bar_bg.pack(fill="x", pady=(6, 0))
            bar_bg.pack_propagate(False)
            bar = tk.Frame(bar_bg, bg=PURPLE, height=5, width=0)
            bar.place(x=0, y=0, relheight=1, relwidth=0)
            self.health_rows[key] = (val, bar, bar_bg)

        tools = self.panel(right, padx=14, pady=14)
        tools.pack(fill="x", pady=(0, 13))
        self.label(tools, "Quick access", 13, FG, True).pack(anchor="w", pady=(0, 10))
        for title, cmd in [
            ("Task Manager", lambda: subprocess.Popen(["taskmgr.exe"])),
            ("Startup apps", lambda: self.open_uri("ms-settings:startupapps")),
            ("Power settings", lambda: self.open_uri("ms-settings:powersleep")),
        ]:
            self.button(tools, title + "  ↗", cmd, compact=True).pack(fill="x", pady=3)

        tips = self.panel(right, padx=14, pady=14)
        tips.pack(fill="both", expand=True)
        self.label(tips, "Small wins", 13, FG, True).pack(anchor="w")
        for tip in [
            "Disable apps you do not need at startup.",
            "Close unused browser tabs and launchers.",
            "Cap game FPS to reduce CPU/GPU load.",
            "Keep laptop vents clear and dust-free."
        ]:
            self.label(tips, "• " + tip, 9, MUTED, wraplength=190, justify="left").pack(anchor="w", pady=(9, 0))

        footer = tk.Frame(main, bg=BG)
        footer.pack(fill="x", pady=(12, 0))
        self.label(footer, "PANDA PC OPTIMIZER", 8, MUTED, True).pack(side="left")
        self.label(footer, "Monitoring only — no hidden tweaks or service disabling", 8, MUTED).pack(side="right")

    def nav_button(self, parent, text, active=False, command=None):
        bg = PURPLE_DARK if active else SIDEBAR
        fg = FG if active else MUTED
        b = tk.Button(parent, text=text, command=command or (lambda: None),
                      bg=bg, fg=fg, activebackground=PURPLE_DARK, activeforeground=FG,
                      relief="flat", bd=0, anchor="w", padx=17, pady=12,
                      font=("Segoe UI", 10, "bold" if active else "normal"),
                      cursor="hand2")
        b.pack(fill="x", padx=10, pady=2)
        return b

    def make_stat_card(self, parent, key, eyebrow, title, subtitle, accent):
        card = self.panel(parent, padx=15, pady=14)
        card.pack(side="left", fill="both", expand=True, padx=(0, 11))
        self.label(card, eyebrow, 8, accent, True).pack(anchor="w")
        line = tk.Frame(card, bg=PANEL)
        line.pack(fill="x", pady=(7, 2))
        value = tk.StringVar(value="—")
        self.stats[key] = value
        tk.Label(line, textvariable=value, bg=PANEL, fg=FG,
                 font=("Segoe UI", 25, "bold")).pack(side="left")
        self.label(line, "%", 11, MUTED, True).pack(side="left", padx=(4, 0), pady=(9, 0))
        self.label(card, title, 10, FG, True).pack(anchor="w", pady=(2, 0))
        self.label(card, subtitle, 8, MUTED, wraplength=210, justify="left").pack(anchor="w", pady=(4, 0))

    def refresh(self):
        if psutil is None:
            messagebox.showerror("Dependency missing", "Please install the required monitoring library.")
            return
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            drive = os.environ.get("SystemDrive", "C:") + "\\"
            disk = psutil.disk_usage(drive).percent
            values = {"cpu": cpu, "ram": ram, "disk": disk}
            for key, val in values.items():
                self.stats[key].set(f"{val:.0f}")
                out, bar, bar_bg = self.health_rows[key]
                out.config(text=f"{val:.0f}%")
                bar.place_configure(relwidth=max(0, min(1, val / 100)))
                bar.config(bg=RED if val >= 90 else ORANGE if val >= 70 else PURPLE)
            self._rows = []
            for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    info = proc.info
                    mem = info.get("memory_info")
                    self._rows.append((proc.cpu_percent(None), info.get("name") or "Unknown",
                                       mem.rss / 1048576 if mem else 0, info["pid"]))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self._rows.sort(reverse=True)
            self.render_processes()
            self.status.set("Updated just now")
            self.status_pill.config(text="● MONITORING", bg="#14251f", fg=GREEN)
        except Exception:
            self.status_pill.config(text="● CHECK SYSTEM", bg="#30241a", fg=ORANGE)

    def render_processes(self):
        if not hasattr(self, "tree"):
            return
        query = self.search.get().strip().lower() if hasattr(self, "search") else ""
        selected = self.tree.selection()
        old_pid = self.tree.set(selected[0], "pid") if selected else None
        self.tree.delete(*self.tree.get_children())
        for cpu, name, ram, pid in self._rows:
            if query and query not in name.lower() and query not in str(pid):
                continue
            iid = self.tree.insert("", "end", values=(name, f"{cpu:.1f}", f"{ram:.0f}", pid))
            if str(pid) == old_pid:
                self.tree.selection_set(iid)

    def schedule_tick(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(15000 if self.mode.get() else 5000, self._scheduled_refresh)

    def _scheduled_refresh(self):
        self.refresh()
        self.schedule_tick()

    def toggle_mode(self):
        self.status_pill.config(text="● GAME MODE" if self.mode.get() else "● MONITORING",
                                bg="#211a35" if self.mode.get() else "#14251f",
                                fg=PURPLE if self.mode.get() else GREEN)
        self.schedule_tick()

    def focus_processes(self):
        self.search_entry.focus_set()
        self.tree.focus_set()

    def show_tips(self):
        messagebox.showinfo("Performance tips",
            "• Review Startup apps in Windows Settings.\n"
            "• Close apps you do not need while gaming.\n"
            "• Lower in-game FPS caps to reduce load.\n"
            "• Keep Windows and graphics drivers updated.\n\n"
            "This app avoids risky registry cleaners and automatic service disabling.")

    def end_task(self):
        if psutil is None:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select a process", "Choose a process in the list first.")
            return
        name, _, _, pid = self.tree.item(sel[0], "values")
        if int(pid) == os.getpid():
            messagebox.showwarning("Protected", "The optimizer cannot close itself from this list.")
            return
        if not messagebox.askyesno("Confirm end task",
                f"End {name} (PID {pid})?\n\nUnsaved work may be lost. Avoid ending Windows or system processes."):
            return
        try:
            proc = psutil.Process(int(pid))
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                if messagebox.askyesno("Still running", "The app is still running. Force close it?"):
                    proc.kill()
            self.refresh()
        except psutil.AccessDenied:
            messagebox.showerror("Access denied", "Windows blocked this action. Leave protected processes alone.")
        except psutil.NoSuchProcess:
            self.refresh()

    def open_uri(self, uri):
        try:
            os.startfile(uri)
        except Exception:
            try:
                subprocess.Popen(["explorer.exe", uri])
            except Exception:
                messagebox.showerror("Could not open", "Windows could not open this settings page.")


if __name__ == "__main__":
    app = PandaOptimizer()
    app.mainloop()

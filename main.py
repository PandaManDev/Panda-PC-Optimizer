import os
import json
import time
import threading
import urllib.request
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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
        self.history = {"cpu": [], "ram": [], "disk": []}
        self.history_window = None
        self.updater_settings = self.load_updater_settings()
        self.sort_key = "cpu"
        self.sort_reverse = True

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
        if self.updater_settings.get("auto_check", False):
            self.after(1200, lambda: self.check_for_updates(show_up_to_date=False))

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
        self.nav_button(sidebar, "⚙   Background services", False, lambda: self.show_services())
        self.nav_button(sidebar, "⇅   Network monitor", False, lambda: self.show_network_monitor())
        self.nav_button(sidebar, "▰   Disk analyzer", False, lambda: self.show_disk_analyzer())
        self.nav_button(sidebar, "🎮   Gaming dashboard", False, lambda: self.show_gaming_dashboard())
        self.nav_button(sidebar, "⚡   Power plans", False, lambda: self.show_power_plans())
        self.nav_button(sidebar, "🧹   Safe cleanup", False, lambda: self.show_safe_cleanup())
        self.nav_button(sidebar, "🚀   Startup apps", False, lambda: self.show_startup_apps())
        self.nav_button(sidebar, "🔋   Battery report", False, lambda: self.create_battery_report())
        self.nav_button(sidebar, "⚙   Windows tools", False, lambda: self.open_uri("ms-settings:"))
        self.nav_button(sidebar, "♡   Performance tips", False, lambda: self.show_tips())
        self.nav_button(sidebar, "▥   Performance history", False, lambda: self.show_history())
        self.nav_button(sidebar, "ⓘ   System report", False, lambda: self.show_report())
        self.nav_button(sidebar, "⟳   App updater", False, lambda: self.show_updater_settings())

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
            self.tree.heading(col, text=title, command=lambda column=col: self.sort_processes(column))
            self.tree.column(col, width=width, anchor="w" if col == "name" else "center",
                             stretch=(col == "name"))
        scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        actions = tk.Frame(process_panel, bg=PANEL)
        actions.pack(fill="x", pady=(12, 0))
        self.label(actions, "Be careful: ending a task can lose unsaved work.", 8, MUTED).pack(side="left")
        self.button(actions, "Reset priority", lambda: self.change_process_priority(False), compact=True).pack(side="right", padx=(6, 0))
        self.button(actions, "Lower priority", lambda: self.change_process_priority(True), compact=True).pack(side="right", padx=(6, 0))
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
            ("Storage settings", lambda: self.open_uri("ms-settings:storagesense")),
            ("Export system report", self.export_report),
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
            for key, val in values.items():
                self.history[key].append(float(val))
                self.history[key] = self.history[key][-60:]
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

    def sort_processes(self, column):
        if column == self.sort_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = column
            self.sort_reverse = column in ("cpu", "ram")
        self.render_processes()

    def export_report(self):
        if psutil is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save Panda system report",
            defaultextension=".txt",
            filetypes=[("Text report", "*.txt")],
            initialfile="Panda-PC-System-Report.txt")
        if not path:
            return
        try:
            vm = psutil.virtual_memory()
            disk_path = os.environ.get("SystemDrive", "C:") + "\\"
            disk = psutil.disk_usage(disk_path)
            cpu_name = os.environ.get("PROCESSOR_IDENTIFIER", "Not reported by Windows")
            lines = [
                "PANDA PC OPTIMIZER — SYSTEM REPORT",
                "=" * 42,
                f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Windows processor: {cpu_name}",
                f"Physical cores: {psutil.cpu_count(logical=False)}",
                f"Logical processors: {psutil.cpu_count(logical=True)}",
                f"CPU usage: {psutil.cpu_percent(interval=0.2):.1f}%",
                f"RAM total: {vm.total / (1024**3):.2f} GB",
                f"RAM available: {vm.available / (1024**3):.2f} GB",
                f"RAM usage: {vm.percent:.1f}%",
                f"System drive usage: {disk.percent:.1f}%",
                f"System drive free: {disk.free / (1024**3):.2f} GB",
                "",
                "TOP PROCESSES (current session sample)",
                "-" * 42,
            ]
            for cpu, name, ram, pid in sorted(self._rows, reverse=True)[:25]:
                lines.append(f"{name} | PID {pid} | CPU {cpu:.1f}% | RAM {ram:.0f} MB")
            with open(path, "w", encoding="utf-8") as report:
                report.write("\n".join(lines) + "\n")
            messagebox.showinfo("Report saved", f"Your system report was saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", f"Could not save the report.\n{exc}")

    def render_processes(self):
        if not hasattr(self, "tree"):
            return
        query = self.search.get().strip().lower() if hasattr(self, "search") else ""
        selected = self.tree.selection()
        old_pid = self.tree.set(selected[0], "pid") if selected else None
        self.tree.delete(*self.tree.get_children())
        rows = list(self._rows)
        if self.sort_key == "name":
            rows.sort(key=lambda row: row[1].lower(), reverse=self.sort_reverse)
        elif self.sort_key == "ram":
            rows.sort(key=lambda row: row[2], reverse=self.sort_reverse)
        elif self.sort_key == "pid":
            rows.sort(key=lambda row: row[3], reverse=self.sort_reverse)
        else:
            rows.sort(key=lambda row: row[0], reverse=self.sort_reverse)
        for cpu, name, ram, pid in rows:
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

    def show_report(self):
        if psutil is None:
            return
        try:
            vm = psutil.virtual_memory()
            cpu_count = psutil.cpu_count(logical=False) or "Unknown"
            logical_count = psutil.cpu_count(logical=True) or "Unknown"
            dt = __import__("datetime")
            boot = dt.datetime.fromtimestamp(psutil.boot_time())
            uptime = dt.timedelta(seconds=int(__import__("time").time() - psutil.boot_time()))
            battery = psutil.sensors_battery()
            battery_text = "Not reported by this PC" if battery is None else f"{battery.percent:.0f}%"
            top = sorted(self._rows, reverse=True)[:8]
            process_text = "\n".join(f"  • {name}: {cpu:.1f}% CPU, {ram:.0f} MB RAM (PID {pid})"
                                     for cpu, name, ram, pid in top) or "  No process data available"
            messagebox.showinfo("Panda system report",
                f"PROCESSOR\n  Physical cores: {cpu_count} | Logical processors: {logical_count}\n"
                f"  Current load: {psutil.cpu_percent(interval=None):.1f}%\n\n"
                f"MEMORY\n  Total: {vm.total / (1024**3):.2f} GB\n"
                f"  Available: {vm.available / (1024**3):.2f} GB\n"
                f"  In use: {vm.percent:.0f}%\n\n"
                f"SYSTEM\n  Booted: {boot.strftime('%Y-%m-%d %H:%M')}\n"
                f"  Uptime: {uptime}\n  Battery: {battery_text}\n\n"
                f"TOP CPU PROCESSES\n{process_text}")
        except Exception as exc:
            messagebox.showerror("Report unavailable", f"Windows could not build the report.\n{exc}")

    def show_history(self):
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.lift()
            self.draw_history()
            return
        win = tk.Toplevel(self)
        self.history_window = win
        win.title("Panda PC Optimizer — Performance history")
        win.geometry("820x520")
        win.minsize(600, 400)
        win.configure(bg=BG)
        header = tk.Frame(win, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 10))
        self.label(header, "Performance history", 19, FG, True).pack(anchor="w")
        self.label(header, "Recent samples from this session • up to 60 readings", 9, MUTED).pack(anchor="w", pady=(3, 0))
        canvas = tk.Canvas(win, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        canvas.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.history_canvas = canvas
        legend = tk.Frame(win, bg=BG)
        legend.pack(fill="x", padx=20, pady=(0, 16))
        for title, color in [("CPU", PURPLE), ("RAM", GREEN), ("Disk", ORANGE)]:
            self.label(legend, "● " + title, 9, color, True).pack(side="left", padx=(0, 18))
        canvas.bind("<Configure>", lambda _event: self.draw_history())
        win.protocol("WM_DELETE_WINDOW", self.close_history)
        self.draw_history()

    def close_history(self):
        if self.history_window is not None:
            self.history_window.destroy()
        self.history_window = None
        self.history_canvas = None

    def draw_history(self):
        canvas = getattr(self, "history_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 220)
        left, right, top, bottom = 48, width - 18, 20, height - 32
        plot_h, plot_w = bottom - top, right - left
        for value in (0, 25, 50, 75, 100):
            y = bottom - plot_h * value / 100
            canvas.create_line(left, y, right, y, fill=BORDER)
            canvas.create_text(left - 10, y, text=str(value), fill=MUTED, anchor="e",
                               font=("Segoe UI", 8))
        for key, color in [("cpu", PURPLE), ("ram", GREEN), ("disk", ORANGE)]:
            data = self.history[key]
            if len(data) < 2:
                canvas.create_text(width / 2, height / 2, text="Collecting samples…",
                                   fill=MUTED, font=("Segoe UI", 11))
                continue
            points = []
            for i, val in enumerate(data):
                x = left + plot_w * i / max(1, len(data) - 1)
                y = bottom - plot_h * max(0, min(100, val)) / 100
                points.extend((x, y))
            canvas.create_line(*points, fill=color, width=2, smooth=True)
        canvas.create_text(left, height - 10, text="Older", fill=MUTED, anchor="w",
                           font=("Segoe UI", 8))
        canvas.create_text(right, height - 10, text="Latest", fill=MUTED, anchor="e",
                           font=("Segoe UI", 8))


    def show_services(self):
        if os.name != "nt":
            messagebox.showinfo("Windows only", "The Background Services Manager is available on Windows.")
            return
        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Background Services")
        win.geometry("1000x620")
        win.minsize(760, 480)
        win.configure(bg=BG)
        self.label(win, "Background Services Manager", 20, FG, True).pack(anchor="w", padx=20, pady=(18, 4))
        self.label(win, "View Windows services. Start/stop is limited to an explicit allowlist of optional services; startup settings are never changed.", 9, MUTED, wraplength=900, justify="left").pack(anchor="w", padx=20, pady=(0, 12))
        self.label(win, "Warning: stopping a service can disable its related feature until it is started again. Run as administrator only if Windows requires it.", 9, ORANGE, wraplength=900, justify="left").pack(anchor="w", padx=20, pady=(0, 12))
        wrap = tk.Frame(win, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        tree = ttk.Treeview(wrap, columns=("display", "name", "state", "start"), show="headings", selectmode="browse")
        for col, title, width in [("display", "SERVICE", 280), ("name", "SERVICE NAME", 170), ("state", "STATUS", 100), ("start", "STARTUP", 100)]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        info = tk.StringVar(value="Loading services…")
        tk.Label(win, textvariable=info, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=20, pady=(0, 8))
        buttons = tk.Frame(win, bg=BG)
        buttons.pack(fill="x", padx=20, pady=(0, 18))
        service_data = {}
        allowed = {"Spooler", "WSearch", "SysMain", "WerSvc", "Fax", "RetailDemo", "MapsBroker", "DiagTrack", "PhoneSvc", "lfsvc"}
        def load_services():
            try:
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                     "Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode | ConvertTo-Json -Compress"],
                    capture_output=True, text=True, timeout=25, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0:
                    raise RuntimeError((result.stderr or "PowerShell could not query services.").strip())
                data = json.loads(result.stdout or "[]")
                if isinstance(data, dict):
                    data = [data]
                service_data.clear()
                tree.delete(*tree.get_children())
                for item in sorted(data, key=lambda x: str(x.get("DisplayName") or x.get("Name") or "").lower()):
                    name = str(item.get("Name") or "")
                    display = str(item.get("DisplayName") or name)
                    iid = tree.insert("", "end", values=(display, name, str(item.get("State") or "Unknown"), str(item.get("StartMode") or "Unknown")))
                    service_data[iid] = item
                info.set(f"{len(data)} services found. Controls are enabled only for approved optional services.")
            except Exception as exc:
                info.set("Could not load services. " + str(exc)[:220])
        def act(action):
            sel = tree.selection()
            item = service_data.get(sel[0]) if sel else None
            if not item:
                messagebox.showinfo("Select a service", "Select a service from the list first.", parent=win)
                return
            name = str(item.get("Name") or "")
            display = str(item.get("DisplayName") or name)
            state = str(item.get("State") or "")
            if name not in allowed:
                messagebox.showwarning("Controls restricted", f"{display} is view-only. Only a small allowlist of optional services can be controlled here.", parent=win)
                return
            if action == "stop" and state.lower() != "running":
                messagebox.showinfo("Already stopped", f"{display} is not running.", parent=win)
                return
            if action == "start" and state.lower() == "running":
                messagebox.showinfo("Already running", f"{display} is already running.", parent=win)
                return
            verb = "stop" if action == "stop" else "start"
            warning = f"{verb.title()} {display} ({name})?\\n\\nStopping it may disable its related feature. Startup settings will not be changed."
            if not messagebox.askyesno(f"Confirm {verb} service", warning, icon="warning", parent=win):
                return
            try:
                result = subprocess.run(["sc.exe", verb, name], capture_output=True, text=True, timeout=20,
                                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0:
                    detail = (result.stdout + "\\n" + result.stderr).strip()
                    messagebox.showerror("Service action failed", (detail or "Windows denied the request. You may need to run the app as administrator.")[:900], parent=win)
                else:
                    messagebox.showinfo("Service command sent", f"Windows accepted the request to {verb} {display}. Refreshing status.", parent=win)
                load_services()
            except Exception as exc:
                messagebox.showerror("Service action failed", str(exc), parent=win)
        self.button(buttons, "↻  Refresh", load_services, compact=True).pack(side="left")
        self.button(buttons, "▶  Start selected", lambda: act("start"), primary=True, compact=True).pack(side="right", padx=(8, 0))
        self.button(buttons, "■  Stop selected", lambda: act("stop"), compact=True).pack(side="right")
        load_services()

    def show_safe_cleanup(self):
        """Preview and remove only old files inside the current user's temp directory."""
        import datetime
        import tempfile

        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Safe Cleanup")
        win.geometry("760x560")
        win.minsize(600, 440)
        win.configure(bg=BG)
        self.label(win, "Safe temporary-file cleanup", 20, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "Scans only your Windows user TEMP folder. By default, only files at least 7 days old are eligible. Downloads, Documents, browser profiles, and Windows system folders are not touched.", 9, MUTED, bg=BG, wraplength=700, justify="left").pack(anchor="w", padx=22, pady=(0, 14))
        folder = tempfile.gettempdir()
        self.label(win, "SCAN LOCATION", 8, PURPLE, True, bg=BG).pack(anchor="w", padx=22)
        self.label(win, folder, 9, MUTED, bg=BG, wraplength=700, justify="left").pack(anchor="w", padx=22, pady=(3, 14))
        summary = tk.StringVar(value="Click Scan to preview eligible files. Nothing is deleted during scanning.")
        tk.Label(win, textvariable=summary, bg=PANEL, fg=FG, font=("Segoe UI", 10), justify="left", anchor="w", wraplength=690, padx=14, pady=12).pack(fill="x", padx=22, pady=(0, 12))
        wrap = tk.Frame(win, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=22, pady=(0, 12))
        tree = ttk.Treeview(wrap, columns=("name", "size", "age"), show="headings")
        for col, title, width in [("name", "FILE / FOLDER", 410), ("size", "SIZE", 100), ("age", "AGE", 100)]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="w" if col == "name" else "center")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        eligible = []

        def fmt_size(n):
            value = float(n)
            for unit in ("B", "KB", "MB", "GB", "TB"):
                if value < 1024 or unit == "TB":
                    return f"{value:.1f} {unit}"
                value /= 1024
            return f"{value:.1f} TB"

        def scan():
            eligible.clear()
            tree.delete(*tree.get_children())
            cutoff = time.time() - 7 * 24 * 60 * 60
            total = 0
            try:
                for root, dirs, files in os.walk(folder, topdown=True):
                    # Avoid traversing reparse points/symlink directories.
                    dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
                    for name in files:
                        path = os.path.join(root, name)
                        try:
                            if os.path.islink(path):
                                continue
                            st = os.stat(path, follow_symlinks=False)
                            if st.st_mtime > cutoff or not os.path.isfile(path):
                                continue
                            eligible.append(path)
                            total += st.st_size
                            age_days = max(7, int((time.time() - st.st_mtime) / 86400))
                            tree.insert("", "end", values=(os.path.relpath(path, folder), fmt_size(st.st_size), f"{age_days} days"))
                        except (OSError, PermissionError):
                            continue
                summary.set(f"Preview: {len(eligible)} old file(s), {fmt_size(total)} potentially reclaimable. Locked files and files that Windows protects will be skipped. No files have been deleted.")
            except Exception as exc:
                summary.set("Scan failed: " + str(exc)[:250])

        def clean():
            if not eligible:
                messagebox.showinfo("Nothing to clean", "Scan first. No eligible files were found.", parent=win)
                return
            total_count = len(eligible)
            if not messagebox.askyesno("Confirm safe cleanup", f"Attempt to delete up to {total_count} files older than 7 days from your user TEMP folder?\n\nOnly the previewed paths will be attempted. Some apps may need temporary files; close apps first. Locked files will be skipped.", icon="warning", parent=win):
                return
            removed = 0
            freed = 0
            failed = 0
            cutoff = time.time() - 7 * 24 * 60 * 60
            for path in list(eligible):
                try:
                    if os.path.commonpath([os.path.abspath(folder), os.path.abspath(path)]) != os.path.abspath(folder):
                        failed += 1
                        continue
                    if os.path.islink(path) or not os.path.isfile(path):
                        failed += 1
                        continue
                    st = os.stat(path, follow_symlinks=False)
                    if st.st_mtime > cutoff:
                        failed += 1
                        continue
                    os.remove(path)
                    removed += 1
                    freed += st.st_size
                except (OSError, PermissionError, ValueError):
                    failed += 1
            eligible.clear()
            scan()
            summary.set(f"Cleanup finished: removed {removed} file(s), freed about {fmt_size(freed)}. Skipped or changed: {failed}. Scan again later to review any remaining files.")
            messagebox.showinfo("Cleanup finished", f"Removed {removed} file(s).\nApproximate space freed: {fmt_size(freed)}\nSkipped/changed files: {failed}", parent=win)

        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=22, pady=(0, 18))
        self.button(actions, "Scan / preview", scan, primary=True).pack(side="left")
        self.button(actions, "Clean previewed files…", clean).pack(side="right")
        self.label(win, "Safety note: this is not a registry cleaner and does not promise a CPU boost. Temporary files currently in use may remain.", 8, ORANGE, bg=BG, wraplength=700, justify="left").pack(anchor="w", padx=22, pady=(0, 12))

    def show_startup_apps(self):
        """Read common Windows startup locations without changing or disabling entries."""
        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Startup Apps")
        win.geometry("900x560")
        win.minsize(680, 420)
        win.configure(bg=BG)
        self.label(win, "Startup apps inspector", 20, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "Read-only view of common Run registry entries and Startup folders. This tool does not disable, delete, or modify startup items.", 9, MUTED, bg=BG, wraplength=840, justify="left").pack(anchor="w", padx=22, pady=(0, 14))
        wrap = tk.Frame(win, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=22, pady=(0, 12))
        tree = ttk.Treeview(wrap, columns=("source", "name", "command"), show="headings")
        for col, title, width in [("source", "LOCATION", 180), ("name", "NAME", 180), ("command", "COMMAND / PATH", 450)]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        status = tk.StringVar(value="Click Refresh to inspect common startup locations.")
        tk.Label(win, textvariable=status, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=840).pack(fill="x", padx=22, pady=(0, 12))

        def scan():
            tree.delete(*tree.get_children())
            count = 0
            errors = []
            try:
                import winreg
                locations = [
                    ("Current user", winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    ("All users", winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    ("Current user (32-bit)", winreg.HKEY_CURRENT_USER, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
                    ("All users (32-bit)", winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
                ]
                for label, hive, key_path in locations:
                    try:
                        with winreg.OpenKey(hive, key_path) as key:
                            index = 0
                            while True:
                                try:
                                    name, value, _kind = winreg.EnumValue(key, index)
                                    tree.insert("", "end", values=(label, str(name), str(value)))
                                    count += 1
                                    index += 1
                                except OSError:
                                    break
                    except OSError:
                        pass
            except Exception as exc:
                errors.append(str(exc))
            startup_dirs = [
                ("Current user Startup", os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")),
                ("All users Startup", os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")),
            ]
            for label, path in startup_dirs:
                if not path or not os.path.isdir(path):
                    continue
                try:
                    for name in os.listdir(path):
                        tree.insert("", "end", values=(label, name, os.path.join(path, name)))
                        count += 1
                except OSError as exc:
                    errors.append(str(exc))
            status.set(f"Found {count} common startup entry/entries. Some apps use other startup mechanisms not shown here." + ((" Notes: " + "; ".join(errors)) if errors else ""))

        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=22, pady=(0, 18))
        self.button(actions, "↻ Refresh startup list", scan, primary=True).pack(side="left")
        self.button(actions, "Open Windows Startup Settings", lambda: self.open_uri("ms-settings:startupapps")).pack(side="right")
        scan()

    def create_battery_report(self):
        """Ask Windows to create a battery report and open it for inspection."""
        if os.name != "nt":
            messagebox.showinfo("Windows only", "Battery reports require Windows powercfg.")
            return
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents")
            os.makedirs(folder, exist_ok=True)
            report_path = os.path.join(folder, "Panda-PC-Battery-Report.html")
            result = subprocess.run(
                ["powercfg.exe", "/batteryreport", "/output", report_path],
                capture_output=True, text=True, timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if result.returncode != 0 or not os.path.isfile(report_path):
                detail = (result.stderr or result.stdout or "Windows could not generate a battery report. Desktop PCs or systems without a supported battery may not provide one.").strip()
                messagebox.showwarning("Battery report unavailable", detail[:900])
                return
            messagebox.showinfo("Battery report created", f"Saved a Windows battery report to:\n{report_path}\n\nIt may include battery capacity and usage history. The report stays on this PC.")
            self.open_uri(report_path)
        except Exception as exc:
            messagebox.showerror("Battery report failed", str(exc)[:900])

    def show_power_plans(self):
        """Inspect Windows power plans and let the user explicitly switch plans."""
        if os.name != "nt":
            messagebox.showinfo("Windows only", "Power plan controls are available on Windows.")
            return
        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Power Plans")
        win.geometry("680x460")
        win.minsize(560, 380)
        win.configure(bg=BG)

        self.label(win, "Windows power plans", 21, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "Choose a power profile for your laptop or desktop. Balanced is a good everyday default; Power saver can reduce performance and power use.", 9, MUTED, bg=BG, wraplength=620, justify="left").pack(anchor="w", padx=22, pady=(0, 18))

        panel = self.panel(win, padx=18, pady=18)
        panel.pack(fill="x", padx=22, pady=(0, 14))
        self.label(panel, "AVAILABLE PLANS", 8, PURPLE, True).pack(anchor="w", pady=(0, 10))
        selected = tk.StringVar(value="")
        combo = ttk.Combobox(panel, textvariable=selected, state="readonly", font=("Segoe UI", 10))
        combo.pack(fill="x", ipady=5)
        current_var = tk.StringVar(value="Checking the active power plan…")
        tk.Label(panel, textvariable=current_var, bg=PANEL, fg=MUTED, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=590).pack(fill="x", pady=(12, 0))
        info_var = tk.StringVar(value="Loading power plans…")
        tk.Label(win, textvariable=info_var, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=620).pack(fill="x", padx=22, pady=(0, 12))

        plans = {}

        def load_plans():
            try:
                result = subprocess.run(
                    ["powercfg.exe", "/list"], capture_output=True, text=True, timeout=12,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0:
                    raise RuntimeError((result.stderr or "powercfg could not list power plans.").strip())
                found = {}
                active_name = None
                import re
                for line in result.stdout.splitlines():
                    match = re.search(r"([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})\s+\((.*?)\)", line)
                    if not match:
                        continue
                    guid, name = match.group(1), match.group(2).strip()
                    found[name] = guid
                    if "*" in line[match.end():]:
                        active_name = name
                plans.clear()
                plans.update(found)
                names = list(found.keys())
                combo["values"] = names
                if active_name:
                    current_var.set("Currently active: " + active_name)
                else:
                    current_var.set("Active plan could not be identified from Windows output.")
                if names:
                    selected.set(active_name if active_name in found else names[0])
                    info_var.set(f"{len(names)} power plan(s) found. Changes apply only after you confirm.")
                else:
                    selected.set("")
                    info_var.set("No plans were detected. Your PC or Windows configuration may not expose standard power plans.")
            except Exception as exc:
                info_var.set("Could not read power plans: " + str(exc)[:250])

        def activate():
            name = selected.get()
            guid = plans.get(name)
            if not guid:
                messagebox.showinfo("Choose a plan", "Select an available power plan first.", parent=win)
                return
            if not messagebox.askyesno("Confirm power plan", f"Switch Windows to '{name}'?\n\nThis changes the active Windows power plan. Performance and battery life may change. You can return to your previous plan here.", parent=win):
                return
            try:
                result = subprocess.run(
                    ["powercfg.exe", "/setactive", guid], capture_output=True, text=True, timeout=12,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0:
                    detail = (result.stderr or result.stdout or "Windows could not activate this plan.").strip()
                    messagebox.showerror("Could not switch plan", detail[:700], parent=win)
                else:
                    messagebox.showinfo("Power plan changed", f"Windows accepted '{name}' as the active power plan.", parent=win)
                load_plans()
            except Exception as exc:
                messagebox.showerror("Power plan failed", str(exc), parent=win)

        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=22, pady=(0, 18))
        self.button(actions, "↻ Refresh plans", load_plans, compact=True).pack(side="left")
        self.button(actions, "Apply selected plan", activate, primary=True).pack(side="right")
        self.label(win, "Tip: Power saver may reduce game performance. Avoid third-party 'ultimate boost' tweaks; this tool only uses Windows powercfg.", 8, ORANGE, bg=BG, wraplength=620, justify="left").pack(anchor="w", padx=22, pady=(0, 16))
        load_plans()


    def show_disk_analyzer(self):
        """Show mounted drive capacity and open Windows storage settings."""
        import shutil

        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Disk Space Analyzer")
        win.geometry("760x540")
        win.minsize(620, 420)
        win.configure(bg=BG)
        self.label(win, "Disk space analyzer", 21, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "Review drive capacity before deciding what to remove. This tool does not delete files.", 9, MUTED, bg=BG, wraplength=680).pack(anchor="w", padx=22, pady=(0, 16))

        wrap = tk.Frame(win, bg=BG)
        wrap.pack(fill="both", expand=True, padx=22, pady=(0, 12))
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def human_size(value):
            value = float(value)
            for unit in ("B", "KB", "MB", "GB", "TB"):
                if value < 1024 or unit == "TB":
                    return f"{value:.1f} {unit}"
                value /= 1024
            return f"{value:.1f} TB"

        def load():
            for child in inner.winfo_children():
                child.destroy()
            found = set()
            try:
                if psutil is not None:
                    partitions = psutil.disk_partitions(all=False)
                    for part in partitions:
                        path = part.mountpoint
                        if path in found:
                            continue
                        found.add(path)
                        try:
                            usage = psutil.disk_usage(path)
                        except (PermissionError, OSError):
                            continue
                        total = usage.total
                        used = usage.used
                        free = usage.free
                        percent = usage.percent
                        card = self.panel(inner, padx=15, pady=13)
                        card.pack(fill="x", pady=(0, 10), padx=(0, 6))
                        heading = tk.Frame(card, bg=PANEL)
                        heading.pack(fill="x")
                        self.label(heading, f"{path}  •  {part.device or 'Drive'}", 11, FG, True).pack(side="left")
                        color = RED if percent >= 90 else ORANGE if percent >= 75 else GREEN
                        self.label(heading, f"{percent:.0f}% used", 10, color, True).pack(side="right")
                        bar = ttk.Progressbar(card, maximum=100, value=percent, mode="determinate")
                        bar.pack(fill="x", pady=(10, 8))
                        self.label(card, f"Used: {human_size(used)}    Free: {human_size(free)}    Total: {human_size(total)}", 9, MUTED).pack(anchor="w")
                else:
                    root = os.environ.get("SystemDrive", "C:") + "\\\\"
                    usage = shutil.disk_usage(root)
                    found.add(root)
                    card = self.panel(inner, padx=15, pady=13)
                    card.pack(fill="x", pady=(0, 10))
                    self.label(card, f"{root} — {human_size(usage.used)} used / {human_size(usage.total)} total", 10, FG).pack(anchor="w")
            except Exception as exc:
                self.label(inner, f"Could not read drive information: {exc}", 10, RED).pack(anchor="w")
            if not found:
                self.label(inner, "No readable mounted drives were found.", 10, MUTED).pack(anchor="w")
            self.label(inner, "Tip: Windows Settings → System → Storage can show temporary files and category breakdowns.", 9, ORANGE, wraplength=620, justify="left").pack(anchor="w", pady=(4, 8))

        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=22, pady=(0, 18))
        self.button(actions, "↻ Refresh drives", load, compact=True).pack(side="left")
        self.button(actions, "Open Windows Storage", lambda: self.open_uri("ms-settings:storagesense"), primary=True).pack(side="right")
        load()

    def show_gaming_dashboard(self):
        """Provide a lightweight, read-only gaming readiness snapshot."""
        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Gaming Dashboard")
        win.geometry("620x510")
        win.minsize(520, 430)
        win.configure(bg=BG)
        self.label(win, "Gaming dashboard", 21, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "A quick readiness check for your current Windows session.", 9, MUTED, bg=BG).pack(anchor="w", padx=22, pady=(0, 16))
        cards = tk.Frame(win, bg=BG)
        cards.pack(fill="x", padx=16)
        values = {}
        for title, key, color in [("CPU LOAD", "cpu", PURPLE), ("RAM USED", "ram", GREEN), ("SYSTEM DRIVE", "disk", ORANGE)]:
            card = self.panel(cards, padx=13, pady=14)
            card.pack(side="left", fill="both", expand=True, padx=6)
            self.label(card, title, 8, color, True).pack(anchor="w")
            values[key] = tk.StringVar(value="Checking…")
            tk.Label(card, textvariable=values[key], bg=PANEL, fg=FG, font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 0))
        tips = self.panel(win, padx=16, pady=14)
        tips.pack(fill="both", expand=True, padx=22, pady=14)
        self.label(tips, "BEFORE YOU LAUNCH A GAME", 9, PURPLE, True).pack(anchor="w", pady=(0, 8))
        recommendations = [
            "Close apps you recognize and do not need; save work first.",
            "Keep enough free disk space for updates and shader caches.",
            "Use Balanced for everyday use; try Best performance only while plugged in.",
            "Avoid ending Windows processes or disabling security software.",
            "Game Mode reduces this app’s own refresh rate; it cannot guarantee higher FPS."
        ]
        for tip in recommendations:
            self.label(tips, "•  " + tip, 9, MUTED, wraplength=520, justify="left").pack(anchor="w", pady=4)
        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=22, pady=(0, 18))
        self.button(actions, "Open Windows Gaming settings", lambda: self.open_uri("ms-settings:gaming"), primary=True).pack(side="left")
        self.button(actions, "Open power plans", self.show_power_plans, compact=True).pack(side="right")

        def update_snapshot():
            if not win.winfo_exists():
                return
            try:
                if psutil is None:
                    values["cpu"].set("N/A")
                    values["ram"].set("N/A")
                    values["disk"].set("N/A")
                else:
                    values["cpu"].set(f"{psutil.cpu_percent(interval=None):.0f}%")
                    mem = psutil.virtual_memory()
                    values["ram"].set(f"{mem.percent:.0f}%")
                    root = os.environ.get("SystemDrive", "C:") + "\\\\"
                    disk = psutil.disk_usage(root)
                    values["disk"].set(f"{disk.percent:.0f}%")
            except Exception:
                for variable in values.values():
                    variable.set("N/A")
            win.after(2500, update_snapshot)

        update_snapshot()

    def show_network_monitor(self):
        """Show lightweight live system-wide network throughput without background polling."""
        if psutil is None:
            messagebox.showerror("Dependency missing", "Install the monitoring dependency to use Network Monitor.")
            return
        try:
            previous = psutil.net_io_counters()
        except Exception as exc:
            messagebox.showerror("Network monitor unavailable", str(exc))
            return

        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — Network Monitor")
        win.geometry("560x390")
        win.minsize(480, 340)
        win.configure(bg=BG)
        self.label(win, "Network activity", 21, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "Live totals and transfer rates for all Windows network adapters.", 9, MUTED, bg=BG).pack(anchor="w", padx=22, pady=(0, 18))

        cards = tk.Frame(win, bg=BG)
        cards.pack(fill="x", padx=16)
        download_var = tk.StringVar(value="0 B/s")
        upload_var = tk.StringVar(value="0 B/s")
        received_var = tk.StringVar(value="—")
        sent_var = tk.StringVar(value="—")
        for title, variable, color in [
            ("DOWNLOAD RATE", download_var, GREEN),
            ("UPLOAD RATE", upload_var, PURPLE),
        ]:
            card = self.panel(cards, padx=16, pady=15)
            card.pack(side="left", fill="both", expand=True, padx=6)
            self.label(card, title, 8, color, True).pack(anchor="w")
            tk.Label(card, textvariable=variable, bg=PANEL, fg=FG,
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(8, 0))

        totals = self.panel(win, padx=16, pady=14)
        totals.pack(fill="x", padx=22, pady=14)
        self.label(totals, "SESSION COUNTERS (WINDOWS NETWORK TOTALS)", 8, MUTED, True).pack(anchor="w", pady=(0, 10))
        for title, variable in [("Received", received_var), ("Sent", sent_var)]:
            row = tk.Frame(totals, bg=PANEL)
            row.pack(fill="x", pady=4)
            self.label(row, title, 10, MUTED).pack(side="left")
            self.label(row, "", 9, MUTED).pack(side="left", expand=True, fill="x")
            tk.Label(row, textvariable=variable, bg=PANEL, fg=FG,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

        self.label(win, "Rates are system-wide and may include background apps. Monitoring stops when this window closes.", 8, MUTED, wraplength=500, justify="left", bg=BG).pack(anchor="w", padx=22, pady=(0, 12))
        state = {"closed": False, "previous": previous, "when": time.monotonic()}

        def human_bytes(value):
            value = max(0.0, float(value))
            units = ("B", "KB", "MB", "GB", "TB")
            for unit in units:
                if value < 1024 or unit == units[-1]:
                    return f"{value:.1f} {unit}"
                value /= 1024
            return f"{value:.1f} TB"

        def tick():
            if state["closed"] or not win.winfo_exists():
                return
            try:
                current = psutil.net_io_counters()
                now = time.monotonic()
                elapsed = max(0.001, now - state["when"])
                download_var.set(human_bytes((current.bytes_recv - state["previous"].bytes_recv) / elapsed) + "/s")
                upload_var.set(human_bytes((current.bytes_sent - state["previous"].bytes_sent) / elapsed) + "/s")
                received_var.set(human_bytes(current.bytes_recv))
                sent_var.set(human_bytes(current.bytes_sent))
                state["previous"] = current
                state["when"] = now
            except Exception:
                download_var.set("Unavailable")
                upload_var.set("Unavailable")
            win.after(1500, tick)

        def close_window():
            state["closed"] = True
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", close_window)
        tick()

    def load_updater_settings(self):
        """Load simple per-user updater preferences, falling back safely on defaults."""
        defaults = {"auto_check": False, "last_seen_release": None}
        try:
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            folder = os.path.join(base, "PandaPCOptimizer")
            os.makedirs(folder, exist_ok=True)
            self.updater_settings_path = os.path.join(folder, "settings.json")
            with open(self.updater_settings_path, "r", encoding="utf-8") as handle:
                saved = json.load(handle)
            if isinstance(saved, dict):
                defaults.update({key: value for key, value in saved.items() if key in defaults})
        except FileNotFoundError:
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            folder = os.path.join(base, "PandaPCOptimizer")
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError:
                pass
            self.updater_settings_path = os.path.join(folder, "settings.json")
        except Exception:
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            self.updater_settings_path = os.path.join(base, "PandaPCOptimizer", "settings.json")
        return defaults

    def save_updater_settings(self):
        try:
            folder = os.path.dirname(self.updater_settings_path)
            os.makedirs(folder, exist_ok=True)
            with open(self.updater_settings_path, "w", encoding="utf-8") as handle:
                json.dump(self.updater_settings, handle, indent=2)
        except Exception as exc:
            messagebox.showerror("Settings not saved", f"Could not save updater preferences.\\n{exc}")

    def show_updater_settings(self):
        win = tk.Toplevel(self)
        win.title("Panda PC Optimizer — App Updater")
        win.geometry("590x430")
        win.minsize(520, 390)
        win.configure(bg=BG)
        self.label(win, "App updater", 22, FG, True, bg=BG).pack(anchor="w", padx=22, pady=(20, 4))
        self.label(win, "Check GitHub Releases for the newest Windows build.", 10, MUTED, bg=BG).pack(anchor="w", padx=22, pady=(0, 18))

        panel = self.panel(win, padx=16, pady=16)
        panel.pack(fill="x", padx=22)
        self.label(panel, "UPDATE PREFERENCES", 9, PURPLE, True).pack(anchor="w", pady=(0, 8))
        auto_var = tk.BooleanVar(value=bool(self.updater_settings.get("auto_check", False)))

        def save_auto():
            self.updater_settings["auto_check"] = bool(auto_var.get())
            self.save_updater_settings()

        tk.Checkbutton(
            panel, text="Check for updates when Panda PC Optimizer opens",
            variable=auto_var, command=save_auto, bg=PANEL, fg=FG,
            selectcolor=PANEL_HI, activebackground=PANEL, activeforeground=FG,
            font=("Segoe UI", 9), wraplength=450, justify="left"
        ).pack(anchor="w", pady=(2, 6))
        self.label(panel, "This preference is saved locally on this Windows account.", 8, MUTED).pack(anchor="w")

        status = tk.StringVar(value="Ready to check for updates.")
        status_panel = self.panel(win, padx=16, pady=14)
        status_panel.pack(fill="both", expand=True, padx=22, pady=14)
        self.label(status_panel, "UPDATE STATUS", 9, PURPLE, True).pack(anchor="w", pady=(0, 8))
        tk.Label(status_panel, textvariable=status, bg=PANEL, fg=FG,
                 font=("Segoe UI", 10), justify="left", wraplength=470,
                 anchor="w").pack(fill="x")

        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=22, pady=(0, 18))
        check_button = self.button(actions, "Check for updates", lambda: self.check_for_updates(status, check_button), primary=True)
        check_button.pack(side="left")
        self.button(actions, "Open releases page", lambda: self.open_uri("https://github.com/PandaManDev/Panda-PC-Optimizer/releases")).pack(side="right")

    def check_for_updates(self, status_var=None, button=None, show_up_to_date=True):
        """Fetch latest release metadata in a worker thread; never auto-download or replace the EXE."""
        if status_var is not None:
            status_var.set("Checking GitHub Releases…")
        if button is not None:
            button.config(state="disabled")

        def worker():
            url = "https://api.github.com/repos/PandaManDev/Panda-PC-Optimizer/releases/latest"
            request = urllib.request.Request(
                url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Panda-PC-Optimizer-Updater"}
            )
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    release = json.loads(response.read().decode("utf-8"))
                if release.get("draft") or release.get("prerelease"):
                    raise ValueError("The latest release is not a stable public release.")
                tag = str(release.get("tag_name") or "Unknown version")
                release_url = str(release.get("html_url") or "https://github.com/PandaManDev/Panda-PC-Optimizer/releases")
                assets = release.get("assets") or []
                exe_asset = next((item for item in assets if str(item.get("name", "")).lower().endswith(".exe")), None)
                download_url = str(exe_asset.get("browser_download_url")) if exe_asset else release_url
                result = {"ok": True, "tag": tag, "url": release_url, "download": download_url}
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}

            def finish():
                if button is not None and button.winfo_exists():
                    button.config(state="normal")
                if status_var is not None:
                    if result["ok"]:
                        status_var.set(f"Latest release found: {result['tag']}\\nOpen the release page to review its notes and download the EXE.\\nNo files have been installed or changed.")
                    else:
                        status_var.set(f"Could not check for updates.\\n{result['error']}\\nCheck your internet connection or open the releases page.")
                if result["ok"]:
                    if status_var is None and show_up_to_date:
                        messagebox.showinfo("Update check complete", f"Latest published version: {result['tag']}\\nOpen the Releases page to review the update and download the EXE.")
                    if status_var is None and not show_up_to_date:
                        # Quiet automatic checks only notify if a newer release is available than the locally recorded last-seen tag.
                        last_seen = self.updater_settings.get("last_seen_release")
                        if last_seen != result["tag"]:
                            self.updater_settings["last_seen_release"] = result["tag"]
                            self.save_updater_settings()
                            self.after(0, lambda: messagebox.showinfo(
                                "Panda PC Optimizer update check",
                                f"Latest published release: {result['tag']}\\nOpen GitHub Releases to review and download it.",
                            ))
                elif status_var is None and show_up_to_date:
                    messagebox.showwarning("Update check failed", result["error"])

            try:
                self.after(0, finish)
            except tk.TclError:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def show_tips(self):
        messagebox.showinfo("Performance tips",
            "• Review Startup apps in Windows Settings.\n"
            "• Close apps you do not need while gaming.\n"
            "• Lower in-game FPS caps to reduce load.\n"
            "• Keep Windows and graphics drivers updated.\n\n"
            "This app avoids risky registry cleaners and automatic service disabling.")

    def change_process_priority(self, lower):
        """Adjust a selected process's scheduling priority, never its CPU affinity or system services."""
        if psutil is None:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select a process", "Choose a process in the list first.")
            return
        name, _, _, pid = self.tree.item(sel[0], "values")
        pid = int(pid)
        protected = {
            "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
            "services.exe", "lsass.exe", "winlogon.exe", "svchost.exe",
            "fontdrvhost.exe", "memory compression"
        }
        if pid <= 4 or name.strip().lower() in protected or pid == os.getpid():
            messagebox.showwarning("Protected process", "This process is protected from priority changes.")
            return
        action = "lower to Below normal" if lower else "reset to Normal"
        explanation = (
            "This changes Windows scheduling priority only. It does not limit CPU usage, and the app may feel slower."
            if lower else
            "This restores the process to Normal scheduling priority."
        )
        if not messagebox.askyesno("Confirm priority change", f"{action}: {name} (PID {pid})?\n\n{explanation}"):
            return
        try:
            proc = psutil.Process(pid)
            priority = getattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS", None) if lower else getattr(psutil, "NORMAL_PRIORITY_CLASS", None)
            if priority is None:
                messagebox.showerror("Not supported", "This priority setting is not supported on this system.")
                return
            proc.nice(priority)
            messagebox.showinfo("Priority updated", f"{name} is now set to {'Below normal' if lower else 'Normal'} priority.")
        except psutil.AccessDenied:
            messagebox.showerror("Access denied", "Windows blocked this change. Try a regular user app rather than a protected process.")
        except psutil.NoSuchProcess:
            messagebox.showinfo("Process ended", "That process is no longer running.")
        except Exception as exc:
            messagebox.showerror("Priority change failed", str(exc))

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

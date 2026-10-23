import os, subprocess, tkinter as tk
from tkinter import ttk, messagebox
try:
    import psutil
except ImportError:
    psutil = None

BG="#101019"; PANEL="#191927"; PURPLE="#9b6bff"; FG="#f4f0ff"; MUTED="#aaa6c2"

class PandaOptimizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panda PC Optimizer")
        self.geometry("960x650"); self.minsize(800,540); self.configure(bg=BG)
        self.game_mode=False
        style=ttk.Style(self); style.theme_use("clam")
        style.configure("Treeview",background=PANEL,foreground=FG,fieldbackground=PANEL,rowheight=27)
        style.configure("Treeview.Heading",background="#29243d",foreground=FG)
        self.build(); self.refresh(); self.after(5000,self.tick)

    def label(self,parent,text,size=10,color=FG,bold=False):
        return tk.Label(parent,text=text,bg=parent.cget("bg"),fg=color,font=("Segoe UI",size,"bold" if bold else "normal"))
    def button(self,parent,text,cmd,primary=False):
        return tk.Button(parent,text=text,command=cmd,bg=PURPLE if primary else "#29243d",fg="white",
          activebackground="#8150e8",relief="flat",bd=0,padx=12,pady=9,cursor="hand2",font=("Segoe UI",10,"bold"))
    def build(self):
        head=tk.Frame(self,bg=BG); head.pack(fill="x",padx=22,pady=18)
        self.label(head,"🐼  Panda PC Optimizer",22,FG,True).pack(anchor="w")
        self.label(head,"Lightweight Windows monitoring and safe optimization tools",10,MUTED).pack(anchor="w",pady=(3,0))
        cards=tk.Frame(self,bg=BG); cards.pack(fill="x",padx=22)
        self.stats={}
        for key,title in [("cpu","CPU USAGE"),("ram","MEMORY USED"),("disk","SYSTEM DRIVE")]:
            c=tk.Frame(cards,bg=PANEL,padx=16,pady=13); c.pack(side="left",fill="x",expand=True,padx=(0,10))
            self.label(c,title,9,MUTED,True).pack(anchor="w")
            var=tk.StringVar(value="—"); self.stats[key]=var
            tk.Label(c,textvariable=var,bg=PANEL,fg=FG,font=("Segoe UI",24,"bold")).pack(anchor="w",pady=5)
        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True,padx=22,pady=16)
        left=tk.Frame(body,bg=PANEL,padx=12,pady=12); left.pack(side="left",fill="both",expand=True,padx=(0,12))
        self.label(left,"Running processes",14,FG,True).pack(anchor="w")
        self.label(left,"Select an app to view resource use",9,MUTED).pack(anchor="w",pady=(2,9))
        self.tree=ttk.Treeview(left,columns=("name","cpu","ram","pid"),show="headings")
        for col,title,width in [("name","PROCESS",240),("cpu","CPU %",70),("ram","RAM MB",80),("pid","PID",65)]:
            self.tree.heading(col,text=title); self.tree.column(col,width=width,anchor="w" if col=="name" else "center")
        self.tree.pack(fill="both",expand=True)
        row=tk.Frame(left,bg=PANEL); row.pack(fill="x",pady=(9,0))
        self.button(row,"Refresh",self.refresh).pack(side="left")
        self.button(row,"End selected task…",self.end_task).pack(side="right")
        right=tk.Frame(body,bg=PANEL,width=230,padx=14,pady=14); right.pack(side="right",fill="y"); right.pack_propagate(False)
        self.label(right,"Quick tools",14,FG,True).pack(anchor="w")
        self.label(right,"Game Mode slows refreshes to reduce this app's own overhead.",9,MUTED).pack(anchor="w",pady=(6,12))
        self.mode=tk.BooleanVar()
        tk.Checkbutton(right,text="Game Mode",variable=self.mode,command=self.toggle_mode,bg=PANEL,fg=FG,selectcolor="#29243d",activebackground=PANEL).pack(anchor="w",pady=(0,8))
        self.button(right,"Startup apps",lambda:self.open_uri("ms-settings:startupapps")).pack(fill="x",pady=4)
        self.button(right,"Task Manager",lambda:subprocess.Popen(["taskmgr.exe"])).pack(fill="x",pady=4)
        self.button(right,"Power settings",lambda:self.open_uri("ms-settings:powersleep")).pack(fill="x",pady=4)
        self.label(right,"CPU-saving tips",11,FG,True).pack(anchor="w",pady=(18,6))
        self.label(right,"• Close unused apps\n• Reduce startup apps\n• Limit game FPS\n• Keep vents clear\n• Avoid ending Windows tasks",9,MUTED).pack(anchor="w")
        self.label(self,"Local-only • No telemetry • Does not disable Windows services",9,MUTED).pack(anchor="w",padx=22,pady=(0,10))
    def refresh(self):
        if psutil is None:
            messagebox.showerror("Dependency missing","Run install.bat first."); return
        try:
            self.stats["cpu"].set(f"{psutil.cpu_percent(interval=0.1):.0f}%")
            self.stats["ram"].set(f"{psutil.virtual_memory().percent:.0f}%")
            drive=os.environ.get("SystemDrive","C:")+"\\"
            self.stats["disk"].set(f"{psutil.disk_usage(drive).percent:.0f}%")
            rows=[]
            for p in psutil.process_iter(["pid","name","memory_info"]):
                try:
                    d=p.info; rows.append((p.cpu_percent(None),d.get("name") or "Unknown",(d["memory_info"].rss/1048576 if d.get("memory_info") else 0),d["pid"]))
                except (psutil.NoSuchProcess,psutil.AccessDenied,psutil.ZombieProcess): pass
            rows.sort(reverse=True)
            selected=self.tree.selection(); old=self.tree.set(selected[0],"pid") if selected else None
            self.tree.delete(*self.tree.get_children())
            for cpu,name,ram,pid in rows[:100]:
                iid=self.tree.insert("","end",values=(name,f"{cpu:.1f}",f"{ram:.0f}",pid))
                if str(pid)==old:self.tree.selection_set(iid)
        except Exception as e: self.title("Panda PC Optimizer — monitoring issue")
    def tick(self):
        self.refresh(); self.after(10000 if self.mode.get() else 5000,self.tick)
    def toggle_mode(self):
        self.title("Panda PC Optimizer — Game Mode" if self.mode.get() else "Panda PC Optimizer")
    def end_task(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("Select a task","Choose a process first."); return
        name,_,_,pid=self.tree.item(sel[0],"values")
        if int(pid)==os.getpid(): return
        if not messagebox.askyesno("Confirm","End "+name+" (PID "+pid+")? Unsaved work may be lost. Do not end Windows/system tasks."): return
        try:
            p=psutil.Process(int(pid)); p.terminate()
            try:p.wait(timeout=3)
            except psutil.TimeoutExpired:
                if messagebox.askyesno("Still running","Force close this app?"):p.kill()
            self.refresh()
        except psutil.AccessDenied: messagebox.showerror("Access denied","Windows blocked this action. Leave protected processes alone.")
        except psutil.NoSuchProcess:self.refresh()
    def open_uri(self,uri):
        try: os.startfile(uri)
        except Exception: subprocess.Popen(["explorer.exe",uri])

if __name__=="__main__":
    app=PandaOptimizer(); app.mainloop()

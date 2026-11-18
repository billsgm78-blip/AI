import json, os, queue, threading, time, webbrowser, subprocess
from pathlib import Path
from urllib.parse import urlsplit
import httpx
import keyring
import pyautogui
import pyperclip
import tkinter as tk
from tkinter import messagebox

APP_NAME = "Jarvis Agent"
KEYRING_SERVICE = "Jarvis Agent"
KEYRING_USER = "desktop-agent"
APPDATA = Path(os.getenv("APPDATA", str(Path.home()))) / "Jarvis"
CONFIG_FILE = APPDATA / "config.json"
APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "explorer": "explorer.exe",
    "paint": "mspaint.exe",
}
ALLOWED_KEYS = {"ctrl", "alt", "shift", "win", "tab", "enter", "esc", "c", "v", "x", "a", "s", "f"}

def read_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_config(server, key):
    server = server.strip().rstrip("/")
    if not server.startswith("https://"):
        raise ValueError("Server manzili https:// bilan boshlanishi kerak.")
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, key.strip())
    APPDATA.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"server": server}, ensure_ascii=False), encoding="utf-8")

def run_task(task):
    action, value = task.get("action"), task.get("value", "")
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError("Buyruq matni juda uzun.")
    if action == "open_url":
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Faqat xavfsiz HTTPS havolalar ochiladi.")
        webbrowser.open(value)
        return "Havola brauzerda ochildi."
    if action == "launch_app":
        name = value.strip().lower()
        if name not in APPS:
            raise ValueError("Bu dastur ruxsat etilgan ro‘yxatda yo‘q.")
        subprocess.Popen([APPS[name]])
        return name + " ishga tushirildi."
    if action == "type_text":
        pyperclip.copy(value)
        pyautogui.hotkey("ctrl", "v")
        return "Matn faol oynaga joylandi."
    if action == "hotkey":
        keys = [item.strip().lower() for item in value.split("+")]
        if not keys or len(keys) > 4 or any(item not in ALLOWED_KEYS for item in keys):
            raise ValueError("Bu tugmalar birikmasiga ruxsat berilmagan.")
        pyautogui.hotkey(*keys)
        return "Tugmalar yuborildi."
    raise ValueError("Noma’lum buyruq.")

class JarvisWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis Agent")
        self.root.geometry("420x250")
        self.root.resizable(False, False)
        self.root.configure(bg="#0b1220")
        self.stop_event = threading.Event()
        self.status_queue = queue.Queue()
        self.server = ""
        self.agent_key = ""
        cfg = read_config()
        self.server = os.getenv("JARVIS_SERVER", cfg.get("server", "https://web-production-2e76118f.up.railway.app"))
        self.agent_key = os.getenv("JARVIS_AGENT_KEY", "") or self.get_saved_key()
        if not self.agent_key:
            self.show_setup()
        else:
            self.show_status()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(500, self.refresh_status)

    def get_saved_key(self):
        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_USER) or ""
        except Exception:
            return ""

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def label(self, parent, text, size=11, color="#e8eefb"):
        return tk.Label(parent, text=text, bg="#0b1220", fg=color, font=("Segoe UI", size))

    def show_setup(self):
        self.clear()
        self.label(self.root, "Jarvis Agent sozlamasi", 18).pack(pady=(22, 5))
        self.label(self.root, "Railway’dagi JARVIS_AGENT_KEY qiymatini kiriting.", 10, "#aab8d0").pack(pady=(0, 12))
        self.label(self.root, "Server manzili").pack(anchor="w", padx=28)
        self.server_var = tk.StringVar(value=self.server)
        tk.Entry(self.root, textvariable=self.server_var, width=51).pack(padx=28, pady=(2, 8))
        self.label(self.root, "Agent kaliti").pack(anchor="w", padx=28)
        self.key_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.key_var, show="•", width=51).pack(padx=28, pady=(2, 12))
        tk.Button(self.root, text="Saqlash va ulash", command=self.save, bg="#477fff", fg="white", relief="flat", padx=14, pady=8).pack()

    def save(self):
        key = self.key_var.get().strip()
        if len(key) < 32:
            messagebox.showerror("Jarvis", "Agent kaliti noto‘g‘ri yoki bo‘sh.")
            return
        try:
            self.server = self.server_var.get().strip().rstrip("/")
            save_config(self.server, key)
            self.agent_key = key
            self.show_status()
            self.start_worker()
        except Exception as exc:
            messagebox.showerror("Jarvis", "Sozlamani saqlab bo‘lmadi: " + str(exc))

    def show_status(self):
        self.clear()
        self.label(self.root, "✦ JARVIS", 22).pack(pady=(28, 6))
        self.status = self.label(self.root, "Ulanmoqda…", 12, "#aab8d0")
        self.status.pack(pady=4)
        self.label(self.root, "Saytdagi tasdiqlangan buyruqlar kompyuterga uzatiladi.", 10, "#aab8d0").pack(pady=8)
        tk.Button(self.root, text="Kalitni o‘zgartirish", command=self.show_setup, bg="#26334a", fg="white", relief="flat", padx=12, pady=7).pack(pady=6)
        if self.agent_key:
            self.start_worker()

    def start_worker(self):
        if getattr(self, "worker_started", False):
            return
        self.worker_started = True
        threading.Thread(target=self.poll, daemon=True).start()

    def poll(self):
        headers = {"X-Jarvis-Agent-Key": self.agent_key}
        while not self.stop_event.is_set():
            try:
                response = httpx.post(self.server + "/agent/next", headers=headers, timeout=30)
                response.raise_for_status()
                task = response.json()
                if task.get("id"):
                    self.status_queue.put("Buyruq bajarilmoqda…")
                    try:
                        result = run_task(task)
                    except Exception as exc:
                        result = "Xato: " + str(exc)
                    httpx.post(self.server + "/agent/result", headers=headers, json={"task_id": task["id"], "result": result}, timeout=20).raise_for_status()
                    self.status_queue.put("Ulandi · " + result)
                else:
                    self.status_queue.put("Ulandi · buyruq kutilmoqda")
            except Exception:
                self.status_queue.put("Serverga ulanib bo‘lmadi · internetni tekshiring")
                time.sleep(4)

    def refresh_status(self):
        try:
            while True:
                self.status.config(text=self.status_queue.get_nowait())
        except queue.Empty:
            pass
        if not self.stop_event.is_set():
            self.root.after(700, self.refresh_status)

    def close(self):
        self.stop_event.set()
        self.root.destroy()

def main():
    root = tk.Tk()
    JarvisWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

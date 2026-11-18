import os,time,webbrowser,subprocess
import httpx
BASE=os.getenv("JARVIS_SERVER","").rstrip("/")
KEY=os.getenv("JARVIS_AGENT_KEY","")
APPS={"notepad":"notepad.exe","calculator":"calc.exe","explorer":"explorer.exe","paint":"mspaint.exe"}
def run(t):
 a,v=t["action"],t["value"]
 if a=="open_url":
  if not v.startswith(("https://","http://")): raise ValueError("Only web URLs are allowed")
  webbrowser.open(v);return "Brauzerda ochildi"
 if a=="launch_app":
  k=v.lower()
  if k not in APPS: raise ValueError("Ruxsat berilmagan dastur")
  subprocess.Popen([APPS[k]]);return k+" ishga tushdi"
 if a=="type_text":
  import pyautogui;pyautogui.write(v,interval=.02);return "Matn kiritildi"
 if a=="hotkey":
  import pyautogui
  keys=[x.strip().lower() for x in v.split("+")]
  if not keys or any(x not in {"ctrl","alt","shift","win","tab","enter","esc","c","v","x","a","s","f"} for x in keys):raise ValueError("Ruxsat berilmagan tugmalar")
  pyautogui.hotkey(*keys);return "Tugmalar yuborildi"
 raise ValueError("Unknown action")
def main():
 if not BASE or not KEY:raise SystemExit("Set JARVIS_SERVER and JARVIS_AGENT_KEY")
 while True:
  try:
   h={"X-Jarvis-Agent-Key":KEY};t=httpx.post(BASE+"/agent/next",headers=h,timeout=25).json()
   if t.get("id"):
    try:r=run(t)
    except Exception as e:r="Xato: "+str(e)
    httpx.post(BASE+"/agent/result",headers=h,json={"task_id":t["id"],"result":r},timeout=20)
  except Exception:time.sleep(5)
if __name__=="__main__":main()

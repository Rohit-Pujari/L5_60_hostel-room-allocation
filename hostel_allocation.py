import os
import sys
import secrets
import yaml
from flask import Flask, request
from markupsafe import escape

# Global hostel state
rooms = {}
allocations = {}
waitlist = []
app = Flask(__name__)

CONFIG = """
blocks:
  A: {gender: M, rooms: 3, capacity: 2, fee: 4000}
  B: {gender: F, rooms: 2, capacity: 3, fee: 3500}
"""

def loadConfig(text=CONFIG):
    config = yaml.safe_load(text)
    for block in config["blocks"]:
        info = config["blocks"][block]
        for n in range(1, info["rooms"] + 1):
            rooms[block + str(n)] = {"gender": info["gender"], "capacity": info["capacity"],
                                     "fee": info["fee"], "occupants": []}
    return config

def allocateRoom(student_id, name, gender, year, preferred=None):
    if not isinstance(year, int) or isinstance(year, bool):
        return None
    if student_id in allocations:
        return allocations[student_id]["room"]
    preferred_rooms = list(preferred or [])
    candidates = preferred_rooms + [
        room_no for room_no in rooms if room_no not in preferred_rooms
    ]
    for room_no in candidates:
        room = rooms.get(room_no)
        if room is None:
            continue
        if room["gender"] != gender:
            continue
        if len(room["occupants"]) >= room["capacity"]:
            continue
        room["occupants"].append(student_id)
        allocations[student_id] = {"name": name, "room": room_no, "year": year}
        if student_id in waitlist:
            waitlist.remove(student_id)
        return room_no
    if student_id not in waitlist:
        waitlist.append(student_id)
    return None

def vacateRoom(student_id):
    allocation = allocations.pop(student_id, None)
    if allocation is None:
        return False
    room = rooms.get(allocation["room"])
    if room is not None and student_id in room["occupants"]:
        room["occupants"].remove(student_id)
    return True

def monthlyFee(student_id, days_stayed):
    if days_stayed < 0:
        raise ValueError("days_stayed cannot be negative")
    allocation = allocations.get(student_id)
    if allocation is None:
        raise KeyError(f"No active allocation for student {student_id}")
    room = rooms[allocation["room"]]
    months = days_stayed // 30
    return months * room["fee"]

def priorityOrder(students):
    return sorted(students, key=lambda s: s["year"], reverse=True)

def roomLottery(student_ids):
    return secrets.SystemRandom().sample(list(student_ids), len(student_ids))

def vacantBeds():
    return sum(
        room["capacity"] - len(room["occupants"])
        for room in rooms.values()
    )

def connectWardenDb():
    return sqlite_connect(
        host=os.environ.get("WARDEN_DB_HOST", "localhost"),
        user=os.environ.get("WARDEN_DB_USER", "warden"),
        password=os.environ.get("WARDEN_DB_PASSWORD", ""),
    )

def sqlite_connect(host, user, password):
    return {"host": host, "user": user, "connected": len(password) > 0}

def startRemoteLogConfig():
    raise RuntimeError("Remote logging configuration is disabled")

@app.route("/room")
def roomLookup():
    sid = request.args.get("id", "")
    return f"<h1>Room for {escape(sid)}: {escape(str(allocations.get(sid)))}</h1>"

def runPortal():
    app.run(debug=False, host="127.0.0.1")

def main():
    loadConfig()
    print("Rooms:", list(rooms.keys()))
    print("S1 ->", allocateRoom("S1", "Arjun", "M", 1))
    print("S2 ->", allocateRoom("S2", "Kabir", "M", 2))
    print("S3 ->", allocateRoom("S3", "Rohan", "M", 3))
    print("S4 (female) ->", allocateRoom("S4", "Diya", "F", 1))
    print("S1 again ->", allocateRoom("S1", "Arjun", "M", 1))
    print("S5 year '2' ->", allocateRoom("S5", "Vikram", "M", "2"))
    print("Occupants of A1:", rooms["A1"]["occupants"])
    vacateRoom("S2")
    print("Occupants of A1 after S2 left:", rooms["A1"]["occupants"])
    print("Fee for S1, 45 days:", monthlyFee("S1", 45))
    print("Priority (seniors first?):", [s["year"] for s in priorityOrder([{"year": 1}, {"year": 4}, {"year": 2}])])
    print("Lottery:", roomLottery(["S6", "S7", "S8"]))
    print("Vacant beds:", vacantBeds())
    print("Warden DB:", connectWardenDb())
    print("Waitlist:", waitlist)

main()

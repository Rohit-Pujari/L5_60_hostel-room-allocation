"""Hostel room allocation utilities and a minimal Flask lookup portal."""

import os
import secrets

import yaml
from flask import Flask, request
from markupsafe import escape

rooms = {}
allocations = {}
waitlist = []
app = Flask(__name__)

CONFIG = """
blocks:
  A: {gender: M, rooms: 3, capacity: 2, fee: 4000}
  B: {gender: F, rooms: 2, capacity: 3, fee: 3500}
"""


def load_config(text=CONFIG):
    """Load room configuration from a YAML string and initialize rooms."""
    config = yaml.safe_load(text)
    if (
        not isinstance(config, dict)
        or not isinstance(config.get("blocks"), dict)
    ):
        raise ValueError("Configuration must contain a blocks mapping")

    rooms.clear()
    for block, info in config["blocks"].items():
        for number in range(1, info["rooms"] + 1):
            room_no = f"{block}{number}"
            rooms[room_no] = {
                "gender": info["gender"],
                "capacity": info["capacity"],
                "fee": info["fee"],
                "occupants": [],
            }
    allocations.clear()
    waitlist.clear()
    return config


def allocate_room(student_id, name, gender, year, preferred=None):
    """Allocate a compatible available room or add the student to the waitlist."""
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
        allocations[student_id] = {
            "name": name,
            "room": room_no,
            "year": year,
        }
        if student_id in waitlist:
            waitlist.remove(student_id)
        return room_no

    if student_id not in waitlist:
        waitlist.append(student_id)
    return None


def vacate_room(student_id):
    """Remove a student from their room and allocation record."""
    allocation = allocations.pop(student_id, None)
    if allocation is None:
        return False
    room = rooms.get(allocation["room"])
    if room is not None and student_id in room["occupants"]:
        room["occupants"].remove(student_id)
    return True


def monthly_fee(student_id, days_stayed):
    """Calculate full-month fees for a student's current room."""
    if days_stayed < 0:
        raise ValueError("days_stayed cannot be negative")
    allocation = allocations.get(student_id)
    if allocation is None:
        raise KeyError(f"No active allocation for student {student_id}")
    room = rooms[allocation["room"]]
    months = days_stayed // 30
    return months * room["fee"]


def priority_order(students):
    """Return students ordered from most senior to most junior."""
    return sorted(
        students,
        key=lambda student: student["year"],
        reverse=True,
    )


def room_lottery(student_ids):
    """Return a randomized ordering of student identifiers."""
    return secrets.SystemRandom().sample(list(student_ids), len(student_ids))


def vacant_beds():
    """Count all unoccupied beds in every room."""
    return sum(
        room["capacity"] - len(room["occupants"])
        for room in rooms.values()
    )


def connect_warden_db():
    """Return placeholder connection metadata without embedding credentials."""
    return sqlite_connect(
        host=os.environ.get("WARDEN_DB_HOST", "localhost"),
        user=os.environ.get("WARDEN_DB_USER", "warden"),
        password=os.environ.get("WARDEN_DB_PASSWORD", ""),
    )


def sqlite_connect(host, user, password):
    """Placeholder for a database connector; never returns the password."""
    return {"host": host, "user": user, "connected": bool(password)}


def start_remote_log_config():
    """Remote logging configuration is disabled for security."""
    raise RuntimeError("Remote logging configuration is disabled")


@app.route("/room")
def room_lookup():
    """Look up a student's room using an escaped HTML response."""
    student_id = request.args.get("id", "")
    allocation = allocations.get(student_id)
    return (
        f"<h1>Room for {escape(student_id)}: "
        f"{escape(str(allocation))}</h1>"
    )


def run_portal():
    """Run the development portal on localhost without debug mode."""
    app.run(debug=False, host="127.0.0.1")


def main():
    """Run a small demonstration of the allocation functions."""
    load_config()
    print("Rooms:", list(rooms.keys()))
    print("S1 ->", allocate_room("S1", "Arjun", "M", 1))
    print("S2 ->", allocate_room("S2", "Kabir", "M", 2))
    print("S3 ->", allocate_room("S3", "Rohan", "M", 3))
    print("S4 (female) ->", allocate_room("S4", "Diya", "F", 1))
    print("S1 again ->", allocate_room("S1", "Arjun", "M", 1))
    print("S5 year '2' ->", allocate_room("S5", "Vikram", "M", "2"))
    print("Occupants of A1:", rooms["A1"]["occupants"])
    vacate_room("S2")
    print("Occupants of A1 after S2 left:", rooms["A1"]["occupants"])
    print("Fee for S1, 45 days:", monthly_fee("S1", 45))
    sample_students = [{"year": 1}, {"year": 4}, {"year": 2}]
    print(
        "Priority (seniors first?):",
        [student["year"] for student in priority_order(sample_students)],
    )
    print("Lottery:", room_lottery(["S6", "S7", "S8"]))
    print("Vacant beds:", vacant_beds())
    print("Warden DB:", connect_warden_db())
    print("Waitlist:", waitlist)


if __name__ == "__main__":
    main()

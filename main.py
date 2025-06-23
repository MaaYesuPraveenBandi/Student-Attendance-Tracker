from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient("mongodb://localhost:27017/")
db = client["attendance_db"]
attendanceRecords = db["attendance_records"]

@app.get("/get-user-attendance")
def getUserAttendance(rollNumber: str):
    sessions = list(attendanceRecords.find({"result." + rollNumber: {"$exists": True}}))
    if not sessions:
        raise HTTPException(status_code=404, detail="No records found for this student")

    batch = sessions[0]["batch"]
    totalSessions = len(sessions)
    attendedSessions = 0
    totalTimeAttended = 0
    totalDuration = 0

    for session in sessions:
        totalDuration += int(session["total_duration"])
        if rollNumber in session["result"]:
            attendedSessions += 1
            totalTimeAttended += int(session["result"][rollNumber])

    percentage = (totalTimeAttended / totalDuration) * 100 if totalDuration > 0 else 0

    return {
        "student": rollNumber,
        "batch": batch,
        "totalSessions": totalSessions,
        "attendedSessions": attendedSessions,
        "totalTimeAttended": totalTimeAttended,
        "totalDuration": totalDuration,
        "percentage": round(percentage, 2)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

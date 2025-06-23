from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import io
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

# Enable CORS for frontend communication (like from localhost:5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["attendance_db"]
attendanceRecords = db["attendance_records"]

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/upload_attendance/")
async def uploadAttendance(
    batch: str = Form(...), 
    dateTime: str = Form(...), 
    file: UploadFile = File(...)
):
    try:
        logger.info(f"Received batch: {batch}")
        logger.info(f"Received dateTime: {dateTime}")

        contents = await file.read()
        decoded = contents.decode("utf-8")
        logger.info(f"CSV content:\n{decoded}")

        df = pd.read_csv(io.StringIO(decoded))

        if "ID" not in df.columns or "Duration" not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'ID' and 'Duration' columns")

        dateTimeObj = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M")

        resultMapping = {str(row["ID"]): int(row["Duration"]) for _, row in df.iterrows()}
        totalDuration = sum(df["Duration"])

        attendanceData = {
            "batch": batch,
            "dateTime": dateTimeObj,
            "result": resultMapping,
            "total_duration": totalDuration
        }

        attendanceRecords.insert_one(attendanceData)

        logger.info("Attendance data stored successfully")
        return {"message": "Attendance stored successfully", "data": attendanceData}

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

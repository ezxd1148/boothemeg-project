"""
api.py

fastapi backend endpoints API
"""

# import local script
# import calendar_api
# import get_notif
# import processing
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

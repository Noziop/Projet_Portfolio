# scripts/migrate_telescopes.py
import sys
import os
from pathlib import Path
import uuid
import json
from sqlalchemy.sql import text
from app.db.session import SessionLocal

def migrate_telescopes():
    session = SessionLocal()
    try:
        telescopes = [
            {
                "id": "HST",
                "name": "Hubble Space Telescope",
                "description": "NASA's visible/UV/near-IR telescope",
                "aperture": "2.4m",
                "focal_length": "57.6m",
                "location": "Low Earth Orbit",
                "instruments": json.dumps({"WFC3": "Wide Field Camera 3", "COS": "Cosmic Origins Spectrograph"}),
                "api_endpoint": "/api/v1/telescopes/hst"
            },
            {
                "id": "JWST",
                "name": "James Webb Space Telescope",
                "description": "NASA's infrared flagship telescope",
                "aperture": "6.5m",
                "focal_length": "131.4m",
                "location": "L2 Lagrange Point",
                "instruments": json.dumps({"NIRCam": "Near Infrared Camera", "MIRI": "Mid-Infrared Instrument"}),
                "api_endpoint": "/api/v1/telescopes/jwst"
            }
        ]
        
        for telescope_data in telescopes:
            stmt = text("""
                INSERT INTO space_telescopes 
                (id, name, description, aperture, focal_length, location, instruments, api_endpoint) 
                VALUES (:id, :name, :description, :aperture, :focal_length, :location, :instruments, :api_endpoint)
            """)
            session.execute(stmt, telescope_data)
            
        session.commit()
        print("Telescopes created successfully!")
        
    finally:
        session.close()

if __name__ == "__main__":
    migrate_telescopes()

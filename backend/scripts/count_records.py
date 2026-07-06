#!/usr/bin/env python3
"""Compter les enregistrements critiques avant/après la sécurisation des médias."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.env_loader import load_backend_env
load_backend_env()

from backend.database import SessionLocal
from backend import models
from backend.core.paths import AppPaths

db = SessionLocal()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads')
MEDIA_DIR = AppPaths.get_user_data_dir() / "media"

patients    = db.query(models.Patient).count()
rdv         = db.query(models.Appointment).count()
actes       = db.query(models.Acte).count()
documents   = db.query(models.DocumentArchive).count()
db.close()

upload_files = sum(len(files) for _, _, files in os.walk(UPLOAD_DIR))
media_files  = sum(len(files) for _, _, files in os.walk(str(MEDIA_DIR))) if MEDIA_DIR.exists() else 0

print(f"Patients    : {patients}")
print(f"RDV         : {rdv}")
print(f"Actes       : {actes}")
print(f"Documents   : {documents}")
print(f"Fichiers uploads : {upload_files}")
print(f"Fichiers media   : {media_files}")

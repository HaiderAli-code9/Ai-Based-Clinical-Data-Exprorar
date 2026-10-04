import pandas as pd
import sqlite3
import os

# Apni CSV files wala path yahan likhein
csv_folder_path = "dataset/hosp" 
icu_folder_path = "dataset/icu"

# SQLite database file banayein
conn = sqlite3.connect("mimic_iv_demo.db")

# Jo files uthani hain unki list
files_to_import = {
    "patients.csv": "hosp",
    "admissions.csv": "hosp",
    "diagnoses_icd.csv": "hosp",
    "transfers.csv": "hosp",   
    "d_icd_diagnoses.csv": "hosp",
    "prescriptions.csv": "hosp",
    "labevents.csv": "hosp",
    "d_labitems.csv": "hosp",
    "icustays.csv": "icu",
    "chartevents.csv" : "icu",
}

for file, folder in files_to_import.items():
    path = os.path.join(csv_folder_path if folder == "hosp" else icu_folder_path, file)
    print(f"Importing {file}...")
    # CSV parh kar SQLite mein daal dein
    df = pd.read_csv(path)
    # Table ka naam .csv hata kar rakh dein (e.g., 'patients.csv' -> 'patients')
    table_name = file.replace(".csv", "")
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Successfully imported {table_name}!")

conn.close()
print("Database ready!")
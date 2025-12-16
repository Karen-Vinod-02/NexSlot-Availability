
import streamlit as st
from sqlalchemy import text, create_engine
import sys

# Mock secrets if needed, or rely on existing secrets.toml if running in same env
# The environment has secrets.toml.

try:
    # Read secrets.toml manually to get url because st.secrets might not work in standalone script easily without streamlit run
    # But I can try to use the logic from app.py
    import toml
    secrets = toml.load("secrets.toml")
    database_url = secrets["connections"]["mysql"]["url"]
    sqlalchemy_url = database_url.replace("mysql://", "mysql+mysqlconnector://")
    engine = create_engine(sqlalchemy_url)

    with engine.connect() as conn:
        result = conn.execute(text("DESCRIBE bookings"))
        print(f"{'Field':<20} {'Type':<20} {'Null':<10} {'Key':<10} {'Default':<20} {'Extra':<10}")
        print("-" * 90)
        for row in result:
             print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3]:<10} {str(row[4]):<20} {str(row[5]):<10}")

except Exception as e:
    print(e)


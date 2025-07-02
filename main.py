import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from amadeus import Client, ResponseError
import time
import os
from dotenv import load_dotenv


load_dotenv()
client_id = os.getenv("CLIENT_KEY")
client_secret = os.getenv("CLIENT_SECRET")



# Debug check
if not client_id or not client_secret:
    raise ValueError("Missing CLIENT_KEY or CLIENT_SECRET in your .env file")


amadeus = Client(
    client_id=client_id,
    client_secret=client_secret
)


routes = [
    ("JFK", "LAX", "jfk_to_lax", "JFK - LAX"),
    ("SIN", "JNB", "sin_to_jnb", "SIN - JNB"),
    ("BOS", "ZRH", "bos_to_zrh", "BOS - ZRH"),
    ("YVR", "SFO", "yvr_to_sfo", "YVR - SFO"),
    ("YYZ", "NRT", "yyz_to_nrt", "YYZ - NRT")
]


conn = sqlite3.connect("flights_data.db")
cursor = conn.cursor()


for _, _, table_name, _ in routes:
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            date TEXT,
            airline TEXT,
            departure_airport TEXT,
            arrival_airport TEXT,
            departure_time TEXT,
            price REAL,
            layovers INTEGER,
            PRIMARY KEY (date, airline, departure_airport, arrival_airport, departure_time)
        )
    """)
conn.commit()

# all days of july
dates = [(datetime(2025, 7, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]


def get_hours(duration):
    duration = duration.replace("PT", "")
    h = m = 0
    if "H" in duration:
        h, duration = duration.split("H")
        h = int(h)
    if "M" in duration:
        m = int(duration.replace("M", ""))
    return round(h + m / 60, 1)


for travel_date in dates:
    for origin, destination, table_name, route_label in routes:
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=travel_date,
                adults=1,
                max=5
            )
            offers = response.data
            records = []

            for offer in offers:
                segments = offer['itineraries'][0]['segments']
                airline = segments[0]['carrierCode']
                dep_airport = segments[0]['departure']['iataCode']
                arr_airport = segments[-1]['arrival']['iataCode']
                dep_time = segments[0]['departure']['at']
                layovers = len(segments) - 1
                price = float(offer['price']['total'])

                record = {
                    "date": travel_date,
                    "airline": airline,
                    "departure_airport": dep_airport,
                    "arrival_airport": arr_airport,
                    "departure_time": dep_time,
                    "price": price,
                    "layovers": layovers
                }

                try:
                    cursor.execute(f"""
                        INSERT INTO {table_name} (
                            date, airline, departure_airport, arrival_airport,
                            departure_time, price, layovers
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, tuple(record.values()))
                    conn.commit()
                    records.append(record)
                except sqlite3.IntegrityError:
                    continue  

            
            df_day = pd.DataFrame(records)
            if not df_day.empty:
                print(f"\n{route_label} on {travel_date}")
                print(df_day.head())

        except ResponseError as e:
            print(f"{route_label} on {travel_date}: {e}")
        time.sleep(1.5)


with pd.ExcelWriter("flight_data_July2025.xlsx", engine="xlsxwriter") as writer:
    for _, _, table_name, label in routes:
        df = pd.read_sql_query(f"""
            SELECT
                date AS Date,
                airline AS Carrier,
                departure_airport AS Origin,
                arrival_airport AS Destination,
                departure_time AS Scheduled_Departure,
                price AS Price_in_Dollars,
                layovers AS Number_of_Layovers
            FROM {table_name}
            WHERE date BETWEEN '2025-07-01' AND '2025-07-31'
            ORDER BY date, price
        """, conn)

        if not df.empty:
            df.to_excel(writer, sheet_name=table_name[:31], index=False)
            writer.sheets[table_name[:31]].set_column("A:G", 20)

conn.close()
print("Done: Data collected and exported.")

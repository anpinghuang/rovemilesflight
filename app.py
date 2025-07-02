import streamlit as st
import sqlite3
import pandas as pd

# Load award chart
award_chart = pd.read_csv('award_chart.csv')

# Points per mile from your Week 1 research
valuation_dict = {
    "AA": 0.016, 
    "TK": 0.007,
    "DL": 0.012,
    "AS": 0.013
}

# Value per mile calculator
def calculate_value_per_mile(cash_price, miles_required):
    if miles_required == 0:
        return 0
    return round(cash_price / miles_required, 2)

# Synthetic routing analysis
def find_synthetic_savings(df, origin, destination, max_layovers=2):
    direct_df = df[(df['Origin'] == origin) & (df['Destination'] == destination) & (df['Number_of_Layovers'] == 0)]
    synthetic_df = df[(df['Origin'] == origin) & (df['Destination'] == destination) & (df['Number_of_Layovers'] <= max_layovers) & (df['Number_of_Layovers'] > 0)]
    
    if direct_df.empty or synthetic_df.empty:
        return None

    direct_price = direct_df['Price_in_Dollars'].min()
    synthetic_price = synthetic_df['Price_in_Dollars'].min()

    if synthetic_price < direct_price:
        savings = round(direct_price - synthetic_price, 2)
        return {
            "direct_price": direct_price,
            "synthetic_price": synthetic_price,
            "savings": savings
        }
    else:
        return None

# Table mapping for each route
table_map = {
    ("JFK", "LAX"): "jfk_to_lax",
    ("SIN", "JNB"): "sin_to_jnb",
    ("BOS", "ZRH"): "bos_to_zrh",
    ("YVR", "SFO"): "yvr_to_sfo",
    ("YYZ", "NRT"): "yyz_to_nrt",
}

# Streamlit UI
st.title("RoveMiles Rewards Redemption Optimizer")

origin = st.selectbox("Origin", ["JFK", "SIN", "BOS", "YVR", "YYZ"])
destination = st.selectbox("Destination", ["LAX", "JNB", "ZRH", "SFO", "NRT"])

if st.button("Analyze"):
    conn = sqlite3.connect('flights_data.db')
    table_name = table_map.get((origin, destination))
    
    if table_name:
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
            WHERE departure_airport = '{origin}' AND arrival_airport = '{destination}'
        """, conn)

        if df.empty:
            st.write("No data available for this route.")
        else:
            st.write("Sample Flights", df)

            # Get miles required and airline from award_chart
            row = award_chart[(award_chart['Origin'] == origin) & (award_chart['Destination'] == destination)]
            if not row.empty:
                airline = row['Airline'].values[0]
                miles_required = row['Miles_Required'].values[0]
                valuation = valuation_dict.get(airline, 0.014)
                
                cheapest = df['Price_in_Dollars'].min()
                value_per_mile = calculate_value_per_mile(cheapest, miles_required)
                
                st.write(f"Cheapest cash price: ${cheapest:.2f}")
                st.write(f"Miles required: {miles_required} miles")
                st.write(f"Approximate value per mile: ${value_per_mile:.2f}")
                st.write(f"Estimated cash value of your miles (using {valuation * 100:.1f}¢/mile): ${miles_required * valuation:.2f}")

                savings_info = find_synthetic_savings(df, origin, destination)
                if savings_info:
                    st.write(f"💡 **Synthetic route savings found!** Save ${savings_info['savings']:.2f}")
                else:
                    st.write("No synthetic route savings found.")
            else:
                st.write("Award chart data not found for this route.")
    else:
        st.write("No data table found for this route.")

    conn.close()

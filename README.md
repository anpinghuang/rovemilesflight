![image](https://github.com/user-attachments/assets/291bf522-03e7-41fd-9923-3499af98601d)

1. **Data collection** (what you gathered and why)
2. **Backend code walkthrough** (`main.py`)
3. **Frontend code walkthrough** (`app.py`)
4. **How to run and use the app**
5. **How to interpret the UI output**


## 1. Project Overview

Build a web tool that helps travelers decide whether to pay cash or redeem airline miles—and spot cheaper “synthetic” (multi-stop) itineraries—for five example international routes.

**the features:**

* Compare cheapest cash fare vs. miles redemption.
* Calculate “value per mile” (¢ value you get when you redeem).
* Highlight any synthetic-routing savings.
* Simple web UI (Streamlit) with dropdowns and results table.



## 2. Data Collection

### 2.1 Flight Data (`main.py` → `flights_data.db`)

* **Routes (the ones we selected in week 2):**

  1. JFK → LAX
  2. SIN → JNB
  3. BOS → ZRH
  4. YVR → SFO
  5. YYZ → NRT

* **Fetched data using:** Amadeus Self-Service API

* **What we store per route:**

  * `date` (YYYY-MM-DD)
  * `airline` (IATA carrier code)
  * `departure_airport`, `arrival_airport`
  * `departure_time`
  * `price` (USD total)
  * `layovers` (number of stops)

* **Why?** Enables comparison of real cash fares to award miles and lets us detect if a multi-stop option can be cheaper than nonstop.



### 2.2 Award Chart Data (`award_chart.csv`)

| Origin | Destination | Airline | Miles\_Required |
|  | -- | - |  |
| JFK    | LAX         | AA      | 6000            |
| SIN    | JNB         | TK      | 45000           |
| BOS    | ZRH         | DL      | 35000           |
| YVR    | SFO         | AS      | 7500            |
| YYZ    | NRT         | AA      | 35000           |

* **Source:** estimated saver-level award charts (AAdvantage, Miles\&Smiles, SkyMiles, Mileage Plan)
* **Why:** Number of miles needed for a one-way economy award on each route. Used to compute “value per mile.”



### 2.3 Valuation Data (hard-coded) (fetched from week 1 )

```python
valuation_dict = {
    "AA": 0.016,   # 1.6¢ per mile
    "TK": 0.007,   # 0.7¢ per mile
    "DL": 0.012,   # 1.2¢ per mile
    "AS": 0.013,   # 1.3¢ per mile
}
```

* **Why:** Estimate cash value of miles for “Estimated cash value of your miles” display.



## 3. Backend Code Walkthrough (`main.py`)

1. **Load API keys** from `.env` (CLIENT\_KEY, CLIENT\_SECRET).

2. **Define routes** and create one SQLite table per route (if not exist).

3. **Iterate** over every day in July 2025 and each route:

   * Call `amadeus.shopping.flight_offers_search.get(...)`.
   * Parse up to 5 offers: extract carrier, price, layovers, times.
   * Insert into the corresponding SQLite table, ignoring duplicates.

4. **Export to Excel** (`flight_data_July2025.xlsx`) for quick human review.



## 4. Frontend Code Walkthrough (`app.py`)

```python
import streamlit as st
import sqlite3
import pandas as pd
```

1. **Load award chart** (CSV) and **valuation dict**.
2. **Define helper functions**:

   * `calculate_value_per_mile(cash_price, miles_required)`
   * `find_synthetic_savings(df, origin, destination)`
3. **Map** each (origin, destination) to its SQLite table name.
4. **Streamlit UI**:

   * `st.selectbox` for Origin & Destination.
   * `st.button("Analyze")` triggers:

     * Connect to `flights_data.db`.
     * Query the correct table for matching rows.
     * If no rows → show “No data available.”
     * Else:

       * Show sample flights table (`st.write(df)`).
       * Look up award-mile requirement from `award_chart.csv`.
       * Compute:

         * **Cheapest cash price** (`df['Price_in_Dollars'].min()`)
         * **Value per mile** = cash\_price / miles\_required
         * **Estimated cash value of miles** = miles\_required × cents\_per\_mile
       * Call `find_synthetic_savings(...)` and display any savings.
     * Close DB connection.



## 5. Running & Using the App

1. **Install dependencies** (omit `sqlite3`):

   ```
   pip install pandas streamlit amadeus python-dotenv xlsxwriter
   ```
   
2. **Collect flight data (skip if using existing db), creating the flights_data.csv** (once):

   ```
   python main.py
   ```
4. **Run UI:**

   ```
   streamlit run app.py
   ```
5. **UI steps:**

   * Select Origin & Destination.
   * Click “Analyze.”
   * Review:

     * Table of flights (carrier, date, price, layovers).
     * Cheapest cash price.
     * Miles required.
     * Value per mile.
     * Estimated cash value of your miles.
     * Synthetic routing savings (if any).



## 6. Interpreting the UI Output

* **Sample Flights table:** shows available cash-fare options.
* **Cheapest cash price:** the lowest fare found.
* **Miles required:** how many miles needed for an award ticket (from award\_chart.csv).
* **Approximate value per mile:** cash\_price ÷ miles\_required (higher = better use of miles).
* **Estimated cash value of your miles:** miles\_required × per-mile valuation (¢).
* **Synthetic savings:** if a multi-stop option is cheaper than nonstop, shows the \$ saved.



### Example Interpretation

> **Cheapest cash price:** \$98
> **Miles required:** 6,000
> **Value per mile:** \$0.016
> **Estimated cash value of your miles:** \$96
> **No synthetic savings:** no cheaper multi-stop option found.
>
> → You’d get \~1.6¢ of value per mile, slightly below AA’s average of 1.6¢–1.7¢, and using miles (worth \$96) vs. paying cash (\$98) are nearly equivalent. No hidden layover deals exist.



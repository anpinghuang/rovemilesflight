![image](https://github.com/user-attachments/assets/291bf522-03e7-41fd-9923-3499af98601d)
Here’s a friendlier, more down-to-earth take on the docs—casual but still clear.

---

# 1. What we collected and why

**Flight data**

* Routes (picked back in Week 2):

  * JFK→LAX, SIN→JNB, BOS→ZRH, YVR→SFO, YYZ→NRT
* Pulled from Amadeus API for every day in July 2025
* Saved into `flights_data.db`, one table per route, with columns:

  * date, airline code, origin, destination, departure time, price (USD), layovers
*  So we have real cash fares to compare against miles and spot if a two-stop trip is actually cheaper than nonstop.

**Award chart** (`award_chart.csv`)

| Origin | Dest | Airline | Miles\_Required |
| ------ | ---- | ------- | --------------- |
| JFK    | LAX  | AA      | 6000            |
| SIN    | JNB  | TK      | 45000           |
| BOS    | ZRH  | DL      | 35000           |
| YVR    | SFO  | AS      | 7500            |
| YYZ    | NRT  | AA      | 35000           |

* Grabbed the “saver” economy rates from each airline’s chart (AA, Turkish, Delta, Alaska)
*   That’s the miles you need to book each route, so we can calculate “value per mile.”

**Valuation numbers** (hard-coded)

```python
valuation_dict = {
  "AA": 0.016,  # 1.6¢/mile
  "TK": 0.007,  # 0.7¢/mile
  "DL": 0.012,  # 1.2¢/mile
  "AS": 0.013,  # 1.3¢/mile
}
```

* Pulled from Week 1 research
* Used to turn miles into “estimated dollar value” in the app

---

# 2. How the backend works (`main.py`)

1. Load your Amadeus credentials (`.env`).
2. Define those five routes, `CREATE TABLE IF NOT EXISTS` for each in SQLite.
3. Loop through July 2025 dates + each route:

   * Call the Amadeus flight search endpoint
   * Take up to five offers, extract carrier, price, stops, times
   * Insert into the right table (skips duplicates)
4. Write out an Excel file (`flight_data_July2025.xlsx`) just for a quick peek

---

# 3. How the frontend works (`app.py`)

```python
import streamlit as st
import sqlite3
import pandas as pd
```

1. Read in `award_chart.csv` and the `valuation_dict`.
2. Define two helpers:

   * `calculate_value_per_mile(cash_price, miles_required)`
   * `find_synthetic_savings(df, origin, dest)`
3. Map each (origin, dest) pair to its SQLite table name.
4. Build a simple Streamlit page:

   * Two dropdowns (origin & destination)
   * “Analyze” button that:

     * Connects to `flights_data.db`
     * Queries the right table
     * If no results, says so
     * Otherwise shows you:

       * A sample of flights (carrier, date, price, layovers)
       * The cheapest cash fare
       * Miles needed (award chart lookup)
       * Value per mile (cash ÷ miles)
       * Estimated mile-value in dollars (miles × valuation)
       * Any synthetic-route savings (multi-stop deal cheaper than nonstop)
     * Closes the DB

---

# 4. Running it

1. **Install** (no need for `sqlite3`—it’s built in):

   ```bash
   pip install pandas streamlit amadeus python-dotenv xlsxwriter
   ```
2. **Fetch data** (only once, unless you want fresh July data):

   ```bash
   python main.py
   ```
3. **Fire up the UI**:

   ```bash
   streamlit run app.py
   ```
4. In your browser:

   * Pick origin & destination
   * Click **Analyze**
   * Read off the results

---

# 5. How to read the results

* **Flights table:** your cash-fare options
* **Cheapest cash price:** the absolute lowest USD fare
* **Miles required:** rows from your saver-level award chart
* **Value per mile:** cash ÷ miles (bigger is better)
* **Estimated cash value of miles:** miles × cents-per-mile valuation
* **Synthetic savings:** shows how much \$ you’d save if there’s a cheaper multi-stop deal

---

### Quick example

> **Cheapest cash price:** \$98
> **Miles required:** 6,000
> **Value per mile:** \$0.016
> **Cash value of miles:** \$96
> **No synthetic savings**

→ You get about 1.6¢ per mile—pretty much in line with AA’s typical value. Using miles vs. paying cash are almost a wash, and no hidden-stop deal beat the nonstop ticket.


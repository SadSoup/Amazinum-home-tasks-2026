# DE Home Task Lecture 13

## How to run the project

To run the pipeline, follow these steps:

### 1. Start the database

```bash
docker compose up -d
```
### 2. Install dependencies

```bash
pip install -r requirements.txt
```
### 3. Run ETL pipeline

```bash
python etl.py
```
## What the pipeline does

1. Loads raw CSV files into pandas DataFrames
2. Cleans data by handling issues listed in the hometask README (I understand that these are not the only possible issues, but my functions focus only on the ones specified in the task)
3. Loads cleaned data into a local PostgreSQL database
4. Creates analytical tables and loads them into PostgreSQL

## Output tables

The pipeline creates the following tables in the PostgreSQL database:

- customers (cleaned customer data)
- orders (cleaned orders data)
- products (cleaned product data)
- order_items (cleaned order items data)

### Analytical tables:

- customer_order_summary
- product_sales_summary
- daily_orders_summary

## Tech Stack

- Python 3.10
- pandas
- PostgreSQL
- Docker Compose
- SQLAlchemy

## Cleaning

All data quality issues were handled using helper functions

* **duplicate primary keys** - handled by helper function `remove_pk_duplicates()`. It removes duplicate primary keys. If `created_at` exists, the newest record is kept. Otherwise, the first occurrence is kept since there is no way to determine which row is newer.
* **missing IDs** - `remove_missing_ids()`. It removes rows with missing IDs because IDs are required for joins and table relationships. Missing IDs cannot be reliably restored or guessed, so such rows are dropped.
* **invalid emails** and **missing emails** - `clean_invalid_emails()`. I decided to keep missing emails as NULL and replace invalid emails with NULL instead of dropping rows, to avoid losing customer data. Other columns can still be used for analysis.
* **invalid timestamps** - `fix_dates()`. I decided to coerce invalid dates to NaT instead of dropping rows, to preserve other columns for analysis
* **negative and zero product prices** and **invalid negative quantity** - `manage_negative_values()`. It replaces negative prices and quantities with NULL as they represent invalid data. I decided to not drop these rows, since other fields may still be useful. Zero prices are kept since they may represent valid business cases (e.g. promotions or free products).
* **unknown order statuses** and **mixed-case status values** - `check_order_status()`. It groups all unexpected order statuses into "unknown" so they are treated as one category in analysis instead of being dropped as invalid data. All status values are converted to lowercase
* **missing references** - `drop_missing_references()`. I decided to drop such rows here since there are only a few of them, so data loss is minimal and should not significantly affect the analysis. This also ensures clean relationships between tables before performing joins. A more advanced approach could include dynamically deciding whether to drop or keep such rows based on the percentage of missing references. This was not implemented in this project, as it would require a different strategy during the analysis stage.

## Analytical output tables

I focused on three main analytical tables:

* **customer_order_summary** - This table helps understand customer behavior. It can show which customers are the most active and valuable, which customers stopped buying, and how long they usually stay active. It can be useful for marketing decisions and customer analysis.
* **product_sales_summary** - This table helps analyze product performance based on completed orders. It shows which products are sold the most and which generate the most revenue. It can be used to identify best-selling products, underperforming products, and support decisions about product assortment, pricing, and promotions.
* **daily_orders_summary** - This table helps analyze how orders and sales change over time (daily view). It can show trends in customer activity, such as busy and slow days, and how revenue and number of sold products change from day to day. This can be useful for understanding seasonality, demand patterns, and overall business performance over time.


Also, I had some other ideas for tables:

- find out which categories of products are the most popular and bring the largest revenue  
- the number of customers from different countries and the number of their orders and revenue. It can also help to decide marketing strategies  
- the distribution of oerder stutuses to control ifthere are some anomalies, which can be a signal of system problems or other issues
- not just daily but also monthly, seasonal and even yearly orders summaries to spot seasonality, or find out other factors that affect sales ((un)successful promotions, other events in the world)  
- analyze dates when customers join to detect success or failure of promotion
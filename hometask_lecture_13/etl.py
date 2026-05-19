import pandas as pd
from sqlalchemy import create_engine

# ==================================================
# DATA LOADING
# ==================================================

order_items = pd.read_csv('data/raw/order_items.csv')
orders = pd.read_csv('data/raw/orders.csv')
customers = pd.read_csv('data/raw/customers.csv')
products = pd.read_csv('data/raw/products.csv')


# ==================================================
# DATA CLEANING FUNCTIONS
# ==================================================

# DATA CLEANING HELPERS

# Remove duplicate primary keys to avoid duplicated records in analysis.
# If created_at exists, keep the newest record.
# Otherwise keep the first occurrence, since there is no way to determine which row is newer.
def remove_pk_duplicates(df, pk_column):
    df = df.copy()
    n_duplicates = df[pk_column].duplicated().sum()
    
    if n_duplicates > 0:
        if 'created_at' in df.columns: # we can save newer record by created_at
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            print(f"Found {n_duplicates} duplicate row(s) for {pk_column}. Removing duplicates and keeping last...")
            return df.sort_values('created_at').drop_duplicates(subset=pk_column, keep='last')
        
        # don't know when record was created, so just keep first one
        print(f"Found {n_duplicates} duplicate rows for {pk_column}. Removing duplicates and keeping first...")
        return df.drop_duplicates(subset=pk_column, keep="first")
    else:
        print(f"No duplicates found for {pk_column}")
        return df
    
# Remove rows with missing IDs because IDs are required for joins and table relationships.
# Missing IDs cannot be reliably restored or guessed, so such rows are dropped.

def remove_missing_ids(df):
    df = df.copy()
    id_columns = [col for col in df.columns if col.endswith('_id')]

    missing_rows = df[id_columns].isnull().any(axis=1).sum()
    if missing_rows > 0:
        print(f"Found {missing_rows} row(s) with missing IDs. Removing rows...")
        df = df.dropna(subset=id_columns) # just drop rows with missing IDs, to avoid issues with joins later
    else:
        print("No missing IDs found.")
    return df


# Decided to keep missing emails as NULL and replace invalid emails with NULL instead of dropping rows,
# to avoid losing customer data. Other columns can still be used for analysis.
def clean_invalid_emails(df):
    df = df.copy()
    
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    missing_mask = customers['email'].isnull()

    invalid_mask = (
        ~df['email'].str.match(email_regex, na=False)
        & ~missing_mask
    )

    n_invalid = invalid_mask.sum()

    if n_invalid > 0:
        print(f"Found {n_invalid} invalid emails. Replacing with NULL values...")

        df.loc[invalid_mask, 'email'] = None

    else:
        print("No invalid emails found.")
    print(f'There are {df["email"].isnull().sum()} missing emails.')
    return df

# Keep original values by coercing invalid dates to NaT instead of dropping rows,
# to preserve other columns for analysis
def fix_dates(df):
    df = df.copy()
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    if df['created_at'].isnull().sum() > 0:
        print(f"Found {df['created_at'].isnull().sum()} invalid dates. Coerced to NaT.")
    else:
        print("No invalid dates found.")
    
    return df

# Replace negative prices and quantities with NULL as they represent invalid data.
# Zero prices are kept since they may represent valid business cases (e.g. promotions or free products).
def manage_negative_values(df, column):
    df = df.copy()
    n_negative = (df[column] < 0).sum()
    df.loc[df[column] < 0, column] = None 

    if n_negative > 0:
        print(f"Found {n_negative} invalid value(s) in column '{column}'. Replacing with NULL values...")
    else:
        print(f"No invalid values found in column '{column}'.")
    return df

# Group all unexpected order statuses into "unknown"
# so they are treated as one category in analysis instead of being dropped as invalid data
def check_order_status(df):
    df = df.copy()
    valid_statuses = {'completed', 'pending', 'cancelled', 'returned'}
    df['order_status'] = df['order_status'].str.lower().fillna("unknown")

    invalid_mask = ~df['order_status'].isin(valid_statuses)
    n_invalid = invalid_mask.sum()
    if n_invalid > 0:
        print(f"Found {n_invalid} invalid order statuses. Please check the data for inconsistencies.")
        df.loc[invalid_mask, 'order_status'] = "unknown"
    else:
        print("All order statuses are valid.")

    return df

# Drop rows with missing references since there are only a few of them.
# If the amount of missing references was larger, it could be better to keep them
# and handle them differently during analysis.
def drop_missing_references(df_ref, df_or, id_col, table_ref_name, table_or_name):
    df_ref = df_ref.copy()

    invalid_mask = ~df_ref[id_col].isin(df_or[id_col])
    n_invalid = invalid_mask.sum()

    if n_invalid > 0:
        print(
            f"Found {n_invalid} row(s) in {table_ref_name} with missing "
            f"{table_or_name} references. Dropping row(s)..."
        )

        df_ref = df_ref[~invalid_mask]
    else:
        print(f"No missing {table_or_name} references found in {table_ref_name}.")

    return df_ref


# TABLE CLEANING PIPELINES

# Apply all cleaning steps for order_items table.
def clean_order_items(order_items=order_items, orders=orders, products=products):
    print(f"Cleaning order_items: {len(order_items)} rows")
    df = order_items.copy()

    df = remove_pk_duplicates(df, 'order_item_id')
    df = remove_missing_ids(df)
    df = drop_missing_references(df, orders, 'order_id', 'order_items', 'orders')
    df = drop_missing_references(df, products, 'product_id', 'order_items', 'products')
    df = manage_negative_values(df, 'quantity')
    print(f"Finished: {len(df)} rows remaining")
    return df

# Apply all cleaning steps for orders table.
def clean_orders(orders=orders, customers=customers):
    print(f"Cleaning orders: {len(orders)} rows")
    df = orders.copy()

    df = remove_pk_duplicates(df, 'order_id')
    df = remove_missing_ids(df)
    df = drop_missing_references(df, customers, 'customer_id', 'orders', 'customers')
    df = fix_dates(df)
    df = check_order_status(df)
    print(f"Finished: {len(df)} rows remaining")
    return df

# Apply all cleaning steps for customers table.
def clean_customers(customers=customers):
    print(f"Cleaning customers: {len(customers)} rows")
    df = customers.copy()

    df = remove_pk_duplicates(df, 'customer_id')
    df = remove_missing_ids(df)
    df = clean_invalid_emails(df)
    df = fix_dates(df)
    print(f"Finished: {len(df)} rows remaining")
    return df

# Apply all cleaning steps for products table.
def clean_products(products=products):
    print(f"Cleaning products: {len(products)} rows")
    df = products.copy()

    df = remove_pk_duplicates(df, 'product_id')
    df = remove_missing_ids(df)
    df = manage_negative_values(df, 'price')
    return df



# ==================================================
# ANALYTICAL TABLE FUNCTIONS
# ==================================================

# This table helps understand customer behavior.
# It can show which customers are the most active and valuable,
# which customers stopped buying, and how long they usually stay active.
# It can be useful for marketing decisions and customer analysis.

def customer_order_summary(cleaned_orders, cleaned_customers, cleaned_order_items, cleaned_products):
    cleaned_orders = cleaned_orders.rename(columns={'created_at': 'order_created_at'})
    
    completed_orders = cleaned_orders[
        cleaned_orders['order_status'] == 'completed'
    ]

    merged = (
    completed_orders
    .merge(cleaned_customers, on='customer_id', how='left')
    .merge(cleaned_order_items, on='order_id', how='left')
    .merge(cleaned_products, on='product_id', how='left'))

    merged['revenue'] = (
    merged['quantity'] * merged['price'])

    summary = (
    merged
    .groupby(
        ['customer_id', 'email', 'country'],
        as_index=False
    )
    .agg(
        total_orders=('order_id', 'nunique'),
        total_items=('quantity', 'sum'),
        total_spent=('revenue', 'sum'),
        first_order_date=('order_created_at', 'min'),
        last_order_date=('order_created_at', 'max')
    ))

    summary['customer_lifetime_days'] = (
        (summary['last_order_date'] - summary['first_order_date']).dt.days
    )  

    return summary 
    

# This table helps analyze product performance based on completed orders.
# It shows which products are sold the most and which generate the most revenue.
# It can be used to identify best-selling products, underperforming products,
# and support decisions about product assortment, pricing, and promotions.

def product_sales_summary(cleaned_orders, cleaned_order_items, cleaned_products):
    
    completed_orders_id = cleaned_orders[cleaned_orders['order_status'] == 'completed']['order_id'].unique() 
    completed_orders = cleaned_order_items[cleaned_order_items['order_id'].isin(completed_orders_id)]
    
    merged = completed_orders.merge(cleaned_products, on='product_id', how='left')

    merged['revenue'] = (
    merged['quantity'] * merged['price'])

    summary = merged.groupby(['product_id', 'name'], as_index=False).agg(
        total_quantity_sold=('quantity', 'sum'),
        total_revenue=('revenue', 'sum'))
    return summary


# This table helps analyze how orders and sales change over time (daily view).
# It can show trends in customer activity, such as busy and slow days,
# and how revenue and number of sold products change from day to day.
# This can be useful for understanding seasonality, demand patterns,
# and overall business performance over time.

def daily_orders_summary(cleaned_orders, cleaned_order_items, cleaned_products):
    completed_orders = cleaned_orders[cleaned_orders['order_status'] == 'completed']
    merged = completed_orders.merge(cleaned_order_items, on = 'order_id').merge(cleaned_products, on = 'product_id')
    
    merged['order_date'] = merged['created_at'].dt.date
    merged['revenue'] = (
        merged['quantity'] * merged['price'])
    summary = merged.groupby('order_date' , as_index=False).agg(total_orders=('order_id', 'nunique'),total_products = ('quantity', 'sum'), total_revenue= ('revenue', 'sum'))

    return summary


# ==================================================
# DATABASE LOADING
# ==================================================

def load_data_to_db(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists='replace', index=False)
    print(f"Loaded {len(df)} rows into table '{table_name}'")

if __name__ == "__main__":
    engine = create_engine('postgresql+psycopg2://user:password@localhost:5433/ht13')

    clean_customers_df = clean_customers()
    load_data_to_db(clean_customers_df, 'customers', engine)

    clean_orders_df = clean_orders()
    load_data_to_db(clean_orders_df, 'orders', engine)

    clean_products_df = clean_products()
    load_data_to_db(clean_products_df, 'products', engine)

    clean_order_items_df = clean_order_items()
    load_data_to_db(clean_order_items_df, 'order_items', engine)
    
    print('\nCreating analytical output tables ...')
    customer_order_summary_df = customer_order_summary(clean_orders_df, clean_customers_df, clean_order_items_df, clean_products_df)
    load_data_to_db(customer_order_summary_df, 'customer_orders', engine)

    product_sales_summary_df = product_sales_summary(clean_orders_df, clean_order_items_df, clean_products_df)
    load_data_to_db(product_sales_summary_df, 'product_sales', engine)

    daily_orders_summary_df = daily_orders_summary(clean_orders_df, clean_order_items_df, clean_products_df)
    load_data_to_db(daily_orders_summary_df, 'daily_orders', engine)
    print('Tables are created.')




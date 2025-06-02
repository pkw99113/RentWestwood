import pandas as pd
import re
import numpy as np

# load the dataset
df = pd.read_csv("zillow_properties_data.csv")

print(df.head())

print(df.info())



# function to extract numeric price from Price column
def extract_price(price_str):
    match = re.search(r"\$([\d,]+)", price_str)
    if match:
        return int(match.group(1).replace(",",""))
    
    return np.nan

# apply function
df['Price_num'] = df['Price'].apply(extract_price)

print(df[['Price', 'Price_num']].head())

# function to extract beds, baths, and sqft from 'Details' column

def extract_details(detail):
    if pd.isna(detail):
        return pd.Series([np.nan, np.nan, np.nan])
    
    bed_match = re.search(r'(\d+) bd', detail)
    bath_match = re.search(r'(\d+) ba', detail)
    sqft_match = re.search(r'(\d[\d,]*) sqft', detail)
    
    beds = int(bed_match.group(1)) if bed_match else (0 if "Studio" in detail else np.nan)
    baths = int(bath_match.group(1) if bath_match else np.nan)
    sqft = int(sqft_match.group(1).replace(',', '')) if sqft_match else np.nan
    
    return pd.Series([beds, baths, sqft])

#apply the function to extract values into new columns
df[['Beds', 'Baths', 'Sqft']] = df['Details'].apply(extract_details)

df = df[df['Beds'].isin([0, 1, 2])]

# remove price outliers for 1, 2 beds
def remove_price_outliers(df, bed_col='Beds', price_col='Price_num'):
    df_filtered = pd.DataFrame()
    for bed_count in df[bed_col].unique():
        subset = df[df[bed_col] == bed_count]
        q1 = subset[price_col].quantile(0.25)
        q3 = subset[price_col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = subset[(subset[price_col] >= lower) & (subset[price_col] <= upper)]
        df_filtered = pd.concat([df_filtered, filtered])
    return df_filtered.reset_index(drop=True)

df = remove_price_outliers(df)

# view outcome
print(df[['Details']].head())
print(df[['Beds', 'Baths', 'Sqft']].head())

# Compute price per sqft
df['Price_per_sqft'] = df['Price_num'] / df['Sqft']

# Filter out extreme values
df = df[(df['Price_per_sqft'] > 1) & (df['Price_per_sqft'] < 6)]

print(df.head())
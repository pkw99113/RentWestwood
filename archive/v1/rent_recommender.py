# rent_recommender.py

import pandas as pd
import joblib

# Load trained model
model = joblib.load("rf_model.pkl")

# Rent recommendation function
def recommend_rent(beds, baths, sqft):
    """
    Predict monthly rent based on number of beds, baths, and square footage.
    Assumes model was trained to predict price per square foot.
    """
    sqft_squared = sqft ** 2
    beds_squared = beds ** 2

    # Format input as a DataFrame
    sample = pd.DataFrame({
        'Beds': [beds],
        'Baths': [baths],
        'Sqft': [sqft],
        'Sqft_squared': [sqft_squared],
        'Beds_squared': [beds_squared]
    })

    # Predict price per sqft
    price_per_sqft = model.predict(sample)[0]
    predicted_rent = price_per_sqft * sqft

    return round(predicted_rent, 2)

# CLI interface for testing
if __name__ == "__main__":
    print("Welcome to the 90024 Rent Estimator!")
    beds = int(input("Enter number of bedrooms: "))
    baths = int(input("Enter number of bathrooms: "))
    sqft = int(input("Enter square footage: "))

    estimate = recommend_rent(beds, baths, sqft)
    print(f"\nEstimated Monthly Rent: ${estimate}")

#exploraty data analysis

import matplotlib.pyplot as plt
import seaborn as sns
from clean_data import df

# distribution of rental prices
plt.figure(figsize=(8,5))
sns.histplot(df['Price_num'], bins=30, kde = True)
plt.title('Distribution of Rental Price')
plt.xlabel('Monthly Rent ($)')
plt.ylabel('Count')
plt.show()

# price vs square footage
plt.figure(figsize=(8,5))
sns.scatterplot(data = df, x= 'Sqft', y = 'Price_num', hue = 'Beds', palette = 'viridis')
plt.title('Rental Price vs. Square Footage')
plt.xlabel('Sqaure Footage')
plt.ylabel('Price ($)')
plt.legend(title = 'Bedrooms')
plt.show()

# boxplot of price by bedroom count
plt.figure(figsize = (8,5))
sns.boxplot(data = df, x = 'Beds', y='Price_num')
plt.title('Price Distribution by Number of Bedrooms')
plt.xlabel('Bedrooms')
plt.ylabel('Price ($)')
plt.show()

# distribution of price per sqft
plt.figure(figsize=(8, 5))
sns.histplot(df['Price_per_sqft'].dropna(), bins=30, kde=True)
plt.title("Distribution of Price per Square Foot")
plt.xlabel("Price per sqft ($)")
plt.ylabel("Count")
plt.show()


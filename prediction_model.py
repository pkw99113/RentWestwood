from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from eda import df
import joblib

# drop rows with missing values 
#df_filtered = df[(df['Price_per_sqft'] > 1) & (df['Price_per_sqft'] < 6)]
df['Sqft_squared'] = df['Sqft'] ** 2
df['Beds_squared'] = df['Beds'] ** 2

df_model = df.dropna(subset = ['Price_num', 'Beds', 'Baths', 'Sqft', 'Sqft_squared', 'Beds_squared'])

# define x and y
X = df_model[['Beds', 'Baths', 'Sqft', 'Sqft_squared', 'Beds_squared']]
y = df_model['Price_per_sqft']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)

# train the model
model = RandomForestRegressor(n_estimators = 100, random_state = 42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = mse ** 0.5
r2 = r2_score(y_test, y_pred)

print(f"MAE: ${mae:.2f}")
print(f"RMSE: ${rmse:.2f}")
print(f"R² Score: {r2:.4f}")

# save trained model to disk
joblib.dump(model, 'rf_model.pkl')
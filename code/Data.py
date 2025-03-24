import kagglehub
import pandas as pd
import openpyxl

from kagglehub import KaggleDatasetAdapter



path = "other_option.csv"
df = pd.read_csv(path)

print(df.head())  # First few rows
print(df.info())  # Column names, data types, and non-null counts
print(df.describe())  # Summary statistics for numerical columns
print(df.isnull().sum())  # Count of missing values per column

missing_city = df[df['Track Preview URL'].isnull()]

# Display the rows with missing data in 'City'

print(missing_city)








import kagglehub
import pandas as pd
import openpyxl

from kagglehub import KaggleDatasetAdapter



path = "data/song_data.csv"
df = pd.read_csv(path)

#print(df.head())  # First few rows
#print(df.info())  # Column names, data types, and non-null counts
#print(df.describe())  # Summary statistics for numerical columns
#print(df.isnull().sum())  # Count of missing values per column

df = df.rename(columns={'topic': 'genre_cluster'})

df.to_excel("song_data.xlsx", index=False)
df.to_csv("song_data.csv", index=False)









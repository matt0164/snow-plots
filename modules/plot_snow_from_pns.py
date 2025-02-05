import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point

# Load snowfall data
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(BASE_DIR, "../data/OKX/raw_metadata/pns_metadata.csv")

df = pd.read_csv(data_file)

# Extract relevant columns (assuming columns exist: 'Latitude', 'Longitude', 'Snowfall')
df = df[['Latitude', 'Longitude', 'Snowfall']].dropna()

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))

# Load a basemap
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Plot the snowfall data
fig, ax = plt.subplots(figsize=(10, 8))
world[world.name == "United States"].plot(ax=ax, color='lightgrey')
gdf.plot(ax=ax, markersize=df['Snowfall']*10, color='blue', alpha=0.6, edgecolor='k')

# Add labels
for x, y, label in zip(df.Longitude, df.Latitude, df.Snowfall):
    ax.text(x, y, str(label), fontsize=8, ha='right', color='darkblue')

plt.title("Snowfall Totals from PNS Data")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)
plt.show()

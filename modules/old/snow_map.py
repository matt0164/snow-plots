"""
This script processes metadata files, filters and validates
geospatial and temporal data, creates an interactive heatmap visualization, and saves
the output as an HTML file.
"""

import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import branca.colormap as cm
from pathlib import Path
import webbrowser
from datetime import datetime, timedelta


def find_latest_metadata_file():
    """
    Finds the latest 'all_stations_all_dates.csv' file in the ALL_STATIONS directory.
    """
    all_stations_dir = Path("../../data/ALL_STATIONS")
    metadata_file = all_stations_dir / "all_stations_all_dates.csv"

    if metadata_file.exists():
        return metadata_file
    else:
        print("❌ No 'all_stations_all_dates.csv' file found in ALL_STATIONS.")
        return None


def get_user_inputs():
    """
    Prompts the user for a date range and station filter.
    """
    date_options = {
        "1": timedelta(days=1),
        "2": timedelta(days=2),
        "7": timedelta(days=7),
        "all": None
    }

    print("\nSelect a date range:")
    print("1 -> Last 24 hours")
    print("2 -> Last 2 days")
    print("7 -> Last week")
    print("all -> All dates")
    date_choice = input("Enter your choice (default: Last 24 hours): ").strip() or "1"

    date_range = date_options.get(date_choice, timedelta(days=1))

    station_code = input("\nEnter a station code to filter by (leave blank for all stations): ").strip() or None

    return date_range, station_code


def generate_snowfall_heatmap():
    """
    Generates an interactive snowfall heatmap with corrected color scaling and clustering.
    """
    metadata_file = find_latest_metadata_file()
    if not metadata_file:
        return

    # Load the dataset
    df = pd.read_csv(metadata_file)

    # Ensure necessary columns exist
    required_columns = ["date", "latitude", "longitude", "value", "Station"]
    for col in required_columns:
        if col not in df.columns:
            print(f"❌ Missing required column: {col}")
            return

    # Convert relevant columns to numeric and datetime values
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["latitude", "longitude", "value", "date"])

    if df.empty:
        print("❌ No valid data available for heatmap generation.")
        return

    # Get user input for filtering
    date_range, station_code = get_user_inputs()

    # Filter by date range
    if date_range:
        start_date = datetime.now() - date_range
        df = df[df["date"] >= start_date]

    # Filter by station code
    if station_code:
        df = df[df["Station"] == station_code]

    if df.empty:
        print("❌ No data available after filtering.")
        return

    # Determine date range for title
    start_date_str = df["date"].min().strftime('%Y-%m-%d')
    end_date_str = df["date"].max().strftime('%Y-%m-%d')

    # Prepare heatmap data
    heat_data = df[["latitude", "longitude", "value"]].values.tolist()

    # Set map center based on mean coordinates
    map_center = [df["latitude"].mean(), df["longitude"].mean()]
    heatmap = folium.Map(location=map_center, zoom_start=7)

    # Define corrected color scale using HEX values
    colormap = cm.LinearColormap(
        colors=["#ADD8E6", "#0000FF", "#9370DB", "#4B0082", "#FFFFFF"],
        vmin=df["value"].min(),
        vmax=df["value"].max(),
        caption="Snowfall Intensity (inches)"
    )

    # Add heatmap layer
    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.5, max_opacity=1).add_to(heatmap)

    # Add colormap legend
    colormap.add_to(heatmap)

    # Save heatmap
    images_dir = Path("../images")
    images_dir.mkdir(exist_ok=True)
    output_file = images_dir / f"snowfall_heatmap_{start_date_str}_{end_date_str}.html"
    heatmap.save(str(output_file))
    print(f"✅ Heatmap saved to '{output_file}'.")

    # Open the heatmap automatically
    webbrowser.open(output_file.absolute().as_uri())


if __name__ == "__main__":
    generate_snowfall_heatmap()

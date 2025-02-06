"""
This script processes metadata files, filters and validates
geospatial and temporal data, creates an interactive heatmap visualization, and saves
the output as an HTML file.

This version specifically processes snowfall data from the last 48 hours for all sites/locations.
If no data is available in the last 48 hours, it adjusts to the most recent available data.
saved file in public directory
"""

import os
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
    all_stations_dir = Path("../data/ALL_STATIONS")
    metadata_file = all_stations_dir / "all_stations_all_dates.csv"

    if metadata_file.exists():
        return metadata_file
    else:
        print("❌ No 'all_stations_all_dates.csv' file found in ALL_STATIONS.")
        return None


def generate_snowfall_heatmap():
    """
    Generates an interactive snowfall heatmap with corrected color scaling for the last 48 hours.
    If no data exists for the last 48 hours, it adjusts to use the most recent available data.
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

    # Set default to last 48 hours, but adjust if no data is found
    start_date = datetime.now() - timedelta(days=2)
    filtered_df = df[df["date"] >= start_date]

    if filtered_df.empty:
        most_recent_date = df["date"].max()
        start_date = most_recent_date - timedelta(days=2)
        filtered_df = df[df["date"] >= start_date]
        print(f"⚠️ No data found for the last 48 hours. Using data from {start_date.strftime('%B %d, %Y')} onward.")

    if filtered_df.empty:
        print("❌ No data available after adjusting for the most recent available data.")
        return

    # Determine date range for title and bottom label
    start_date_str = filtered_df["date"].min().strftime('%B %d, %Y')
    end_date_str = filtered_df["date"].max().strftime('%B %d, %Y')

    # Prepare heatmap data
    heat_data = filtered_df[["latitude", "longitude", "value"]].values.tolist()

    # Set map center based on mean coordinates
    map_center = [filtered_df["latitude"].mean(), filtered_df["longitude"].mean()]
    heatmap = folium.Map(location=map_center, zoom_start=7)

    # Define corrected color scale using HEX values
    colormap = cm.LinearColormap(
        colors=["#ADD8E6", "#0000FF", "#9370DB", "#4B0082", "#FFFFFF"],
        vmin=filtered_df["value"].min(),
        vmax=filtered_df["value"].max(),
        caption="Snowfall Intensity (inches)"
    )

    # Add heatmap layer
    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.5, max_opacity=1).add_to(heatmap)

    # Add colormap legend
    colormap.add_to(heatmap)

    # Add title and source
    title_html = f"""
        <h3 align="center" style="font-size:20px"><b>Snowfall from Last 48 Hours</b></h3>
        <p align="center" style="font-size:14px">Source: National Weather Service (NOAA) Public Information Statements</p>
    """
    heatmap.get_root().html.add_child(folium.Element(title_html))

    # Add date range at the bottom
    date_range_html = f"""
        <div style="position: fixed; bottom: 10px; right: 10px; background: white; padding: 5px; font-size: 12px; text-align: right;">
            <b>Report covers:</b><br>
            {start_date_str} - {end_date_str}
        </div>
    """
    heatmap.get_root().html.add_child(folium.Element(date_range_html))

    # Add snowfall labels with clustering to prevent overlap
    marker_cluster = MarkerCluster().add_to(heatmap)
    for _, row in filtered_df.iterrows():
        report_date = row["date"].strftime('%B %d, %Y')  # Example: "February 5, 2025"
        folium.Marker(
            [row["latitude"], row["longitude"]],
            icon=folium.DivIcon(html=f"""
                <div style='font-size: 18px; font-weight: bold; color: black; text-align: center;'>
                    {row['value']:.1f}"<br>
                    <span style='font-size: 12px; color: gray;'>{report_date}</span>
                </div>
            """)
        ).add_to(marker_cluster)

    # Save heatmap
    images_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../public")))
    images_dir.mkdir(exist_ok=True)

    # output_file = images_dir / f"snowfall_heatmap_{start_date_str}_{end_date_str}.html"
    output_file = images_dir / "snowfall_heatmap_current.html"
    heatmap.save(str(output_file))
    print(f"✅ Heatmap saved to '{output_file}'")

    # Open the heatmap automatically
    webbrowser.open(output_file.absolute().as_uri())


if __name__ == "__main__":
    generate_snowfall_heatmap()
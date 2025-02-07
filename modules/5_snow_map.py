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
    required_columns = ["date", "latitude", "longitude", "value", "Station", "description"]
    for col in required_columns:
        if col not in df.columns:
            print(f"❌ Missing required column: {col}")
            return

    # Ensure that 'description' is a string column
    df["description"] = df["description"].astype(str)

    # Filter out rows that do not contain "SNOW" in the description column
    df = df[df['description'].str.contains('SNOW', case=False, na=False)]

    # Convert relevant columns to numeric and datetime values
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["latitude", "longitude", "value", "date"])

    # Ensure the "Station" column is a string
    df["Station"] = df["Station"].astype(str)

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

    # Coordinates for the center of Manhattan
    manhattan_center = [40.7831, -73.9712]

    # Create the map with a zoom level that shows the NYC metro area
    heatmap = folium.Map(location=manhattan_center, zoom_start=10)

    # Set map center based on mean coordinates
    # map_center = [filtered_df["latitude"].mean(), filtered_df["longitude"].mean()]
    # heatmap = folium.Map(location=map_center, zoom_start=10)

    # Define corrected color scale using HEX values
    colormap = cm.LinearColormap(
        colors=["#ADD8E6", "#0000FF", "#9370DB", "#4B0082", "#FFFFFF"],
        vmin=filtered_df["value"].min(),
        vmax=filtered_df["value"].max(),
        caption="Snowfall Intensity (inches)"
    )

    # Define gradient based on vmin and vmax -- new section
    gradient = {
        0: "#ADD8E6",
        0.25: "#0000FF",
        0.5: "#9370DB",
        0.75: "#4B0082",
        1: "#FFFFFF"
    }

    # Ensure that all values in the heat_data are valid floats and not integers
    heat_data = [
        [float(lat), float(lon), float(value)] for lat, lon, value in heat_data
    ]

    # Add heatmap layer
    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.5, max_opacity=1).add_to(heatmap)

    # Add colormap legend
    colormap.add_to(heatmap)

    # Add title and source
    title_html = f"""
        <h3 align="center" style="font-size:20px"><b>Snowfall from Last 48 Hours</b></h3>
        <p align="center" style="font-size:14px">Source: National Weather Service (NOAA) Public Information Statements</p>
        <p align="center" style="font-size:14px">Not for commercial redistribution without credit to Emkay Ventures LLC</p>
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
    marker_cluster = MarkerCluster(
        disableClusteringAtZoom=1  # Disable clustering at zoom level 10 and higher
    ).add_to(heatmap)

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
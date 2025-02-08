from pathlib import Path
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import branca.colormap as cm
import webbrowser
from datetime import datetime, timedelta


def find_latest_metadata_file():
    """
    Finds the latest 'all_stations_all_dates.csv' file in the ALL_STATIONS directory.
    Returns the file's path if it exists, otherwise returns None.
    """
    all_stations_dir = Path(__file__).resolve().parent.parent / "data" / "ALL_STATIONS"
    metadata_file = all_stations_dir / "all_stations_all_dates.csv"

    if metadata_file.exists():
        return metadata_file
    else:
        print("❌ No 'all_stations_all_dates.csv' file found in ALL_STATIONS.")
        return None


def generate_snowfall_heatmap():
    """
    Generates an interactive snowfall heatmap for the last 48 hours. If no data
    exists for the last 48 hours, it adjusts to use the most recent available data.
    Saves the heatmap as an HTML file and opens it in the default web browser.
    """
    # Find the latest metadata file
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

    # Clean and filter DataFrame
    df["description"] = df["description"].astype(str)  # Ensure 'description' is a string
    df = df[df['description'].str.contains('SNOW', case=False, na=False)]  # Only rows with "SNOW" in description
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "value", "date"])  # Drop invalid rows
    df["Station"] = df["Station"].astype(str)  # Ensure 'Station' column is a string

    if df.empty:
        print("❌ No valid data available for heatmap generation.")
        return

    # Default to last 48 hours, adjust if no data exists
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

    # Prepare heatmap data
    heat_data = filtered_df[["latitude", "longitude", "value"]].values.tolist()

    # Define the map
    heatmap = folium.Map(location=[40.7831, -73.9712], zoom_start=10)  # Default: Manhattan center

    # Define color scale using HEX values
    colormap = cm.LinearColormap(
        colors=["#ADD8E6", "#0000FF", "#9370DB", "#4B0082", "#FFFFFF"],
        vmin=filtered_df["value"].min(),
        vmax=filtered_df["value"].max(),
        caption="Snowfall Intensity (inches)"
    )

    # Heatmap layer
    heat_data = [[float(lat), float(lon), float(value)] for lat, lon, value in heat_data]
    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.5, max_opacity=1).add_to(heatmap)

    # Add colormap legend
    colormap.add_to(heatmap)

    # Add title to the map
    title_html = """
        <h3 align="center" style="font-size:20px"><b>Snowfall from Last 48 Hours</b></h3>
        <p align="center" style="font-size:14px">Source: National Weather Service (NOAA)</p>
    """
    heatmap.get_root().html.add_child(folium.Element(title_html))

    # Add date range at the bottom
    start_date_str = filtered_df["date"].min().strftime('%B %d, %Y')
    end_date_str = filtered_df["date"].max().strftime('%B %d, %Y')
    date_range_html = f"""
        <div style="position: fixed; bottom: 10px; right: 10px; background: white; padding: 5px; font-size: 12px;">
            <b>Report covers:</b><br>
            {start_date_str} - {end_date_str}
        </div>
    """
    heatmap.get_root().html.add_child(folium.Element(date_range_html))

    # Add map markers using MarkerCluster
    marker_cluster = MarkerCluster(disableClusteringAtZoom=10).add_to(heatmap)
    for _, row in filtered_df.iterrows():
        report_date = row["date"].strftime('%B %d, %Y')
        folium.Marker(
            [row["latitude"], row["longitude"]],
            icon=folium.DivIcon(html=f"""
                <div style='font-size: 14px; font-weight: bold; text-align: center; color: black;'>
                    {row['value']:.1f}"<br>
                    <span style='font-size: 12px; color: gray;'>{report_date}</span>
                </div>
            """)
        ).add_to(marker_cluster)

    # Save the heatmap
    output_dir = Path(__file__).resolve().parent.parent / "public"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "snowfall_heatmap_current.html"
    heatmap.save(output_file)
    print(f"✅ Heatmap saved to '{output_file}'")

    # Open the heatmap automatically in the default browser
    webbrowser.open(output_file.absolute().as_uri())


if __name__ == "__main__":
    generate_snowfall_heatmap()

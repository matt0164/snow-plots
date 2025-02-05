"""This script processes metadata files, filters and validates
    geospatial and temporal data, creates an interactive heatmap visualization, and saves
    the output as an HTML file. """

import os
import pandas as pd
import folium
from folium.plugins import HeatMap
import branca.colormap as cm
from pathlib import Path
import webbrowser

def find_metadata_files(base_path="data"):
    """
    Find metadata files in the given base directory.

    This function searches recursively for ``pns_metadata.csv`` files within
    the ``raw_metadata`` subdirectories of each station folder. If a
    metadata file is found, the station name (inferred from the parent
    folder name of the ``raw_metadata`` directory) and the corresponding
    CSV file path are added to the returned dictionary.

    :param base_path: The base directory to begin the search. Defaults to
        "data".
    :type base_path: str
    :return: A dictionary where the keys are station names and the values
        are the paths to the corresponding ``pns_metadata.csv`` files.
    :rtype: dict
    """
    metadata_files = {}
    base_dir = Path(base_path)

    # Recursively search for pns_metadata.csv files within each station folder
    for station_dir in base_dir.glob("*/raw_metadata"):
        station_name = station_dir.parent.name  # Infer station name from parent folder
        csv_file = station_dir / "pns_metadata.csv"
        if csv_file.exists():
            metadata_files[station_name] = csv_file

    return metadata_files


def load_metadata(selected_stations, metadata_files):
    """
    Loads metadata by reading specified files and optionally filtering by selected stations.
    Combines all metadata files into a single DataFrame with an additional column
    indicating the station name.

    :param selected_stations: List of station names to filter the metadata. If empty or
        None, all stations will be included.
    :type selected_stations: list[str] | None
    :param metadata_files: Dictionary mapping station names to their corresponding
        file paths containing metadata.
    :type metadata_files: dict[str, str]
    :return: Combined pandas DataFrame of metadata from the specified stations. If no
        matching station metadata is available, returns None.
    :rtype: pandas.DataFrame | None
    """
    data_frames = []

    for station, file_path in metadata_files.items():
        if not selected_stations or station in selected_stations:
            df = pd.read_csv(file_path)
            df['Station'] = station  # Add station as a column for context
            data_frames.append(df)

    if not data_frames:
        return None

    return pd.concat(data_frames, ignore_index=True)


def select_stations(metadata_files):
    """
    Interactive function to select specific weather stations from a given metadata file dictionary. The function lists
    all available stations and captures user input for their selection. Users can select a single station, opt to use
    data from all stations, or re-input if an invalid choice is made.

    :param metadata_files: A dictionary containing metadata of weather stations, where keys represent station names.
    :type metadata_files: dict
    :return: A list containing the name of the selected station(s) or None if all stations are selected.
    :rtype: list or None
    """
    print("\nAvailable Stations:")
    for i, station in enumerate(metadata_files.keys(), start=1):
        print(f"{i} -> {station}")

    print("\n0 -> Use data from all stations")
    choice = input("Enter your choice (e.g., 1 for the first station, 0 for all): ").strip()

    if choice == "0":
        return None  # All stations
    elif choice.isdigit():
        index = int(choice) - 1
        if index in range(len(metadata_files)):  # Validate choice
            selected_station = list(metadata_files.keys())[index]
            return [selected_station]

    print("Invalid input. Please try again.")
    return select_stations(metadata_files)


def main():
    """
    Execute the main function to perform a series of data processing tasks for generating a
    snowfall intensity heatmap. This script processes metadata files, filters and validates
    geospatial and temporal data, creates an interactive heatmap visualization, and saves
    the output as an HTML file.

    :return: None
    """
    # Find all metadata files in the data directory
    base_path = "../data"  # Adjusted for relative path from /modules
    metadata_files = find_metadata_files(base_path=base_path)

    if not metadata_files:
        print("No metadata files found. Please check the directory structure.")
        return

    # Prompt the user to select stations or use all
    selected_stations = select_stations(metadata_files)

    if selected_stations:
        print(f"Loading data for station(s): {', '.join(selected_stations)}...")
    else:
        print("Loading data for all stations...")

    # Load the selected metadata
    data = load_metadata(selected_stations, metadata_files)
    if data is None or data.empty:
        print("No data is available for the selected station(s).")
        return

    # Extract relevant columns
    latitude_col = pd.to_numeric(data.iloc[:, 7], errors="coerce")
    longitude_col = pd.to_numeric(data.iloc[:, 8], errors="coerce")
    snowfall_col = pd.to_numeric(data.iloc[:, 10], errors="coerce")
    date_col = pd.to_datetime(data.iloc[:, 9], errors="coerce")  # Assuming column 9 stores dates

    # Filter out invalid data
    valid_data = data.dropna(subset=[data.columns[7], data.columns[8], data.columns[10], data.columns[9]])

    # Remove invalid (NaT) dates from the date column
    valid_date_col = date_col.dropna()

    # Check if valid dates are available
    if valid_date_col.empty:
        print("No valid date information is available in the dataset.")
        return  # Exit the program gracefully

    # Determine date range for the dataset
    start_date = valid_date_col.min().strftime('%Y-%m-%d')  # Earliest date
    end_date = valid_date_col.max().strftime('%Y-%m-%d')  # Latest date

    # Prepare data for the heatmap (latitude, longitude, snowfall intensity)
    heat_data = list(zip(valid_data.iloc[:, 7], valid_data.iloc[:, 8], valid_data.iloc[:, 10]))

    # Set the map center based on mean coordinates
    map_center = [latitude_col.mean(), longitude_col.mean()]
    heatmap = folium.Map(location=map_center, zoom_start=7)

    # Add heatmap layer
    HeatMap(heat_data, radius=15, blur=10, max_zoom=9).add_to(heatmap)

    # Add a colormap legend
    colormap = cm.LinearColormap(
        colors=["lightblue", "blue", "darkblue", "purple"],
        vmin=min(snowfall_col),
        vmax=max(snowfall_col),
        caption="Snowfall Intensity (inches)"
    )
    colormap.add_to(heatmap)

    # Add tooltips for snowfall observations
    for lat, lon, snowfall in zip(valid_data.iloc[:, 7], valid_data.iloc[:, 8], valid_data.iloc[:, 10]):
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=f"<div style='font-size: 10px; color: black;'>{snowfall:.1f}\"</div>")
        ).add_to(heatmap)

    # Save heatmap to the /images directory with appended date range
    images_dir = Path("../images")  # Adjusted relative to /modules
    images_dir.mkdir(exist_ok=True)  # Ensure the /images folder exists

    # Define the output file path with dates in the name
    output_file = images_dir / f"snowfall_heatmap_{start_date}_{end_date}.html"
    heatmap.save(str(output_file))
    print(f"✅ Heatmap generated and saved to '{output_file}'.")

    # Automatically open the file in the default browser
    webbrowser.open(output_file.absolute().as_uri())  # Opens the file via its URI


# Entry point
if __name__ == "__main__":
    main()

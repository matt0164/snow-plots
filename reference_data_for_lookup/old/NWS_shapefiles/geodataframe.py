import geopandas as gpd
import os

# Path to the shapefile directory
SHAPEFILE_DIR = '/reference_data_for_lookup/NWS_shapefiles'  # Replace with the actual path
SHAPEFILE_NAME = 'z_18mr25.shp'  # Replace with the actual shapefile name
SHAPEFILE_PATH = os.path.join(SHAPEFILE_DIR, SHAPEFILE_NAME)


def load_shapefile(shapefile_path):
    """
    Load a shapefile into a GeoDataFrame using GeoPandas.
    Args:
        shapefile_path (str): Path to the shapefile.
    Returns:
        GeoDataFrame: Loaded shapefile as a GeoDataFrame.
    """
    try:
        gdf = gpd.read_file(shapefile_path)
        print("Shapefile loaded successfully.")
        return gdf
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None


def analyze_shapefile(gdf):
    """
    Analyze the contents of a GeoDataFrame.
    Args:
        gdf (GeoDataFrame): The GeoDataFrame to analyze.
    """
    # Display basic information
    print("\nGeoDataFrame Info:")
    print(gdf.info())

    # Display the first few rows
    print("\nFirst Few Rows:")
    print(gdf.head())

    # Display the CRS (Coordinate Reference System)
    print("\nCoordinate Reference System (CRS):")
    print(gdf.crs)

    # Display unique values in key columns
    print("\nUnique Values in Key Columns:")
    key_columns = ['STATE', 'ZONE', 'NAME']  # Update with columns present in your shapefile
    for column in key_columns:
        if column in gdf.columns:
            print(f"{column}: {gdf[column].unique()}")


def main():
    # Load the shapefile
    gdf = load_shapefile(SHAPEFILE_PATH)

    if gdf is not None:
        # Analyze the GeoDataFrame
        analyze_shapefile(gdf)


if __name__ == "__main__":
    main()

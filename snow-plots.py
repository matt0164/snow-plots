import os
import pandas as pd
import matplotlib.pyplot as plt
import pytesseract
from PIL import Image


# Function to extract snowfall data from a single image
def extract_snowfall_data(image_path):
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    # Load the image
    img = Image.open(image_path)

    # Use pytesseract to do OCR on the image
    text = pytesseract.image_to_string(img)

    # Process the text to extract relevant data
    data = []
    for line in text.splitlines():
        if line.strip():  # Skip empty lines
            # Example format: "City: 5, 10, 15"
            parts = line.split(':')
            if len(parts) > 1:
                city_data = parts[1].strip().split(',')
                # Ensure we have low, mid (expected), and high values
                if len(city_data) == 3:
                    try:
                        data.append([parts[0].strip()] + [float(x) for x in city_data])
                    except ValueError:
                        continue  # Skip rows with invalid numeric data

    return pd.DataFrame(data, columns=["City", "Low End (90%)", "Expected", "High End (10%)"])


# Function to merge data from three images
def merge_snowfall_data(low_path, mid_path, high_path):
    # Extract data from each image
    low_df = extract_snowfall_data(low_path)
    mid_df = extract_snowfall_data(mid_path)
    high_df = extract_snowfall_data(high_path)

    # Merge all data into a single DataFrame
    combined_df = low_df.copy()
    combined_df["Expected"] = mid_df["Expected"] if not mid_df.empty else None
    combined_df["High End (10%)"] = high_df["High End (10%)"] if not high_df.empty else None

    return combined_df


# Function to validate the paths dynamically
def validate_paths(*paths):
    missing_files = []
    for path in paths:
        if not os.path.exists(path):
            missing_files.append(path)
    if missing_files:
        raise FileNotFoundError(f"The following files are missing: {', '.join(missing_files)}")


# Paths to your images
# Note: Update these paths based on the location of your image files
low_image_path = 'images/low.png'  # Use relative or absolute paths accordingly
mid_image_path = 'images/mid.png'
high_image_path = 'images/high.png'

# Validate file paths before proceeding
validate_paths(low_image_path, mid_image_path, high_image_path)

# Combine data from all images
df = merge_snowfall_data(low_image_path, mid_image_path, high_image_path)

# Replace non-numeric values if necessary and fill gaps
for column in ["Low End (90%)", "Expected", "High End (10%)"]:
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(1)

# Define sub-regions as in your original script
sub_regions = {
    "Hudson Valley": ["Kingston", "Sundown", "Monticello", "Middletown", "Cold Spring"],
    "New Jersey (NJ)": ["West Milford", "Paramus", "Newark", "Somerville"],
    "Westchester and CT": ["New City", "White Plains", "Danbury", "Bridgeport"],
    "Long Island (LI)": ["Stony Brook", "Syosset", "Westhampton", "Islip", "Montauk"],
    "NYC and 5 Boroughs": ["NYC", "JFK"]
}

# Generate plots for each sub-region
for region, cities in sub_regions.items():
    sub_region_data = df[df["City"].isin(cities)]
    if sub_region_data.empty:
        print(f"No data available for region: {region}")
        continue

    box_data = []
    valid_labels = []
    for city in cities:
        if city in sub_region_data["City"].values:
            box_data.append([
                sub_region_data.loc[sub_region_data["City"] == city, "Low End (90%)"].values[0],
                sub_region_data.loc[sub_region_data["City"] == city, "Expected"].values[0],
                sub_region_data.loc[sub_region_data["City"] == city, "High End (10%)"].values[0]
            ])
            valid_labels.append(city)

    plt.figure(figsize=(12, 6))
    plt.boxplot(box_data, labels=valid_labels, vert=True, patch_artist=True)
    plt.title(f"Snowfall Probabilistic Forecast - {region}", fontsize=16)
    plt.xlabel("Cities", fontsize=12)
    plt.ylabel("Snowfall (inches)", fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(f"snowfall_{region.replace(' ', '_').lower()}.png", bbox_inches="tight")
    plt.show()

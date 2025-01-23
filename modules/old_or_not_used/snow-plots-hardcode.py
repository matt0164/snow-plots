import pandas as pd
import matplotlib.pyplot as plt

# Data
data = {
    "City": [
        "Kingston", "Sundown", "Monticello", "Middletown", "Cold Spring", "Danbury",
        "West Milford", "New City", "White Plains", "Paramus", "NYC", "Newark",
        "Bridgeport", "Stony Brook", "Syosset", "Westhampton", "Islip", "Montauk", "JFK"
    ],
    "Low End (90%)": [2, 2, 3, 4, 3, 3, 4, 3, 2, 2, 1, 3, 2, "<1", "<1", 1, 1, 2, 1],
    "Expected": [5, 5, 6, 7, 7, 7, 6, 6, 5, 5, 5, 5, 4, 4, 4, 3, 3, 4, 4],
    "High End (10%)": [13, 13, 13, 14, 13, 12, 14, 11, 10, 10, 10, 10, 9, 11, 10, 11, 10, 12, 10]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Replace non-numeric values (e.g., "<1") with 1 for plotting purposes
for column in ["Low End (90%)", "Expected", "High End (10%)"]:
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(1)  # Replace "<1" or other errors with 1

# Define sub-regions
sub_regions = {
    "Hudson Valley": ["Kingston", "Sundown", "Monticello", "Middletown", "Cold Spring"],
    "New Jersey (NJ)": ["West Milford", "Paramus", "Newark", "Somerville"],
    "Westchester and CT": ["New City", "White Plains", "Danbury", "Bridgeport"],
    "Long Island (LI)": ["Stony Brook", "Syosset", "Westhampton", "Islip", "Montauk"],
    "NYC and 5 Boroughs": ["NYC", "JFK"]
}

# Source details
source = "Weather Forecast Office, New York, NY"
issue_time = "Issued: Jan 19, 2025, 5:16 AM EST"

# Generate plots for each sub-region
for region, cities in sub_regions.items():
    # Filter data for the current sub-region
    sub_region_data = df[df["City"].isin(cities)]
    if sub_region_data.empty:
        print(f"No data available for region: {region}")
        continue

    # Prepare data for boxplot and adjust labels dynamically
    box_data = []
    valid_labels = []  # To ensure labels match the data
    for city in cities:
        if city in sub_region_data["City"].values:
            box_data.append([
                sub_region_data.loc[sub_region_data["City"] == city, "Low End (90%)"].values[0],
                sub_region_data.loc[sub_region_data["City"] == city, "Expected"].values[0],
                sub_region_data.loc[sub_region_data["City"] == city, "High End (10%)"].values[0]
            ])
            valid_labels.append(city)

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.boxplot(box_data, labels=valid_labels, vert=True, patch_artist=True)

    # Customize the plot
    plt.title(f"Snowfall Probabilistic Forecast - {region}", fontsize=16)
    plt.xlabel("Cities", fontsize=12)
    plt.ylabel("Snowfall (inches)", fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Add source and issue time as a footnote
    plt.figtext(0.5, -0.05, f"Source: {source} | {issue_time}", wrap=True, ha="center", fontsize=10)
    plt.tight_layout()

    # Save and show the plot
    plt.savefig(f"snowfall_{region.replace(' ', '_').lower()}.png", bbox_inches="tight")
    plt.show()

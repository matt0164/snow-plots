#/ this script doesnt really work. The best version I had going hard coded
# the data directly into the code and was saved in pythonmista mobile app
# I then tried creating a jupyter notebook with pytesseract here:
# https://nb.anaconda.cloud/jupyterhub/user/8ece0aa4-262a-4a1b-b1e2-7dee49ed6760/lab?redirects=1
# when i tried to incorporate OCR image recognition the entire thing failed
# a version of this called snow-plots-simple will work

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(image_path):
    """Preprocess the image to improve OCR results."""
    img = Image.open(image_path)
    img = img.convert("L")  # Convert to grayscale
    img = img.filter(ImageFilter.MedianFilter())  # Apply median filter to reduce noise
    img = img.point(lambda x: 0 if x < 128 else 255, "1")  # Binarize (black and white)
    return img


def extract_snowfall_data(image_path):
    """Extract snowfall data from an image."""
    print(f"Processing image: {image_path}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    # Preprocess the image
    img = preprocess_image(image_path)

    # Use pytesseract to do OCR on the image
    text = pytesseract.image_to_string(img)
    print(f"Extracted text from {image_path}:\n{text[:500]}")  # Debugging

    # Regex patterns for cities and snowfall data
    city_pattern = re.compile(r"^[A-Za-z\s]+$")  # Matches city names
    snowfall_pattern = re.compile(r"(\d+)'")  # Matches snowfall values (e.g., 3')

    # Parse the text
    data = []
    for line in text.splitlines():
        if line.strip():  # Skip empty lines
            parts = line.split()
            city = " ".join(word for word in parts if city_pattern.match(word))
            snowfall = [int(match.group(1)) for match in snowfall_pattern.finditer(line)]
            if city and len(snowfall) == 1:  # Ensure one city and one snowfall value per line
                data.append([city.strip(), snowfall[0]])

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=["City", "Snowfall"])
    print(f"Extracted DataFrame from {image_path}:\n{df}")  # Debugging
    return df


def merge_snowfall_data(low_path, mid_path, high_path):
    """Merge data from low, mid, and high snowfall images."""
    low_df = extract_snowfall_data(low_path)
    mid_df = extract_snowfall_data(mid_path)
    high_df = extract_snowfall_data(high_path)

    # Merge data into one DataFrame
    combined_df = pd.merge(low_df, mid_df, on="City", how="outer", suffixes=("_Low", "_Mid"))
    combined_df = pd.merge(combined_df, high_df, on="City", how="outer")
    combined_df.rename(columns={"Snowfall": "High_End"}, inplace=True)

    print(f"Combined DataFrame:\n{combined_df}")  # Debugging
    return combined_df


# Paths to your images
low_image_path = "../../images/data_source_images_snow_plots_tesseract/low.png"
mid_image_path = "../../images/data_source_images_snow_plots_tesseract/mid.png"
high_image_path = "../../images/data_source_images_snow_plots_tesseract/high.png"

# Ensure the files exist
for path in [low_image_path, mid_image_path, high_image_path]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

# Merge snowfall data
df = merge_snowfall_data(low_image_path, mid_image_path, high_image_path)

# Validate and clean numeric columns
for col in ["Snowfall_Low", "Snowfall_Mid", "High_End"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

print(f"Final DataFrame:\n{df}")

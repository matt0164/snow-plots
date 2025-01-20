import os
from pathlib import Path

class Config:
    BASE_PROJECT_DIR = Path("/Users/mattalevy/PycharmProjects/snow-plots")
    CONFIG_FILE = BASE_PROJECT_DIR / "config.txt"
    BASE_URL = "https://forecast.weather.gov/product.php"
    MAX_PAGES = 5

    def __init__(self):
        self.base_dir = self.BASE_PROJECT_DIR
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.data_dir / "backup"
        self.pns_reports_file = self.data_dir / "pns_reports.csv"
        self.log_file = self.base_dir / "logs" / "scraping.log"
        self.setup_directories()

    def setup_directories(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.log_file.parent, exist_ok=True)

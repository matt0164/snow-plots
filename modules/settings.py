from pathlib import Path


class Config:
    """
    Configuration class to manage project-wide settings and directories.
    This ensures all required directories and files are created dynamically.
    """

    BASE_PROJECT_DIR = Path(__file__).resolve().parent.parent  # Dynamically set the project root directory
    CONFIG_FILE = BASE_PROJECT_DIR / "config.txt"
    BASE_URL = "https://forecast.weather.gov/product.php"
    MAX_PAGES = 5

    def __init__(self):
        self.base_dir = self.BASE_PROJECT_DIR
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.data_dir / "backup"
        self.pns_reports_file = self.data_dir / "pns_reports.csv"
        self.logs_dir = self.base_dir / "logs"
        self.log_file = self.logs_dir / "scraping.log"

        self.setup_directories()

    def setup_directories(self):
        """
        Sets up required directories for the project.
        """
        # Create required directories if they do not exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

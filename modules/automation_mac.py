import schedule
import time
import subprocess

def job():
    # Adjust the interpreter path if needed.
    subprocess.run(["/usr/bin/python3", "/Users/mattalevy/PycharmProjects/snow-plots/modules/0_master.py"])

# Schedule the job to run every hour
schedule.every().hour.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
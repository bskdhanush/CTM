import crash_count_controller
import os, json

if __name__ == "__main__":
    day_couter=crash_count_controller.load_day_count()
    print(day_couter)
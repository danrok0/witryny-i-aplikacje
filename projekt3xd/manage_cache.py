from utils.data_storage import DataStorage
import argparse

def main():
    parser = argparse.ArgumentParser(description='Manage API cache files')
    parser.add_argument('--clear', action='store_true', help='Clear all cache files')
    parser.add_argument('--clear-weather', action='store_true', help='Clear weather cache files')
    parser.add_argument('--clear-trails', action='store_true', help='Clear trails cache files')
    parser.add_argument('--merge', action='store_true', help='Merge all cache files into one')
    parser.add_argument('--output', type=str, default='all_data.json', help='Output file for merged data')
    args = parser.parse_args()

    storage = DataStorage()

    if args.clear:
        storage.clear_cache()
        print("All cache files cleared.")
    elif args.clear_weather:
        for city in ["gdansk", "warszawa", "krakow", "wroclaw"]:
            storage.clear_cache(f"weather_{city}.json")
        print("Weather cache files cleared.")
    elif args.clear_trails:
        for city in ["gdansk", "warszawa", "krakow", "wroclaw"]:
            storage.clear_cache(f"trails_{city}.json")
        print("Trails cache files cleared.")
    elif args.merge:
        storage.merge_json_files(args.output)
        print(f"All data merged into {args.output}")
    else:
        print("No action specified. Use --help for usage information.")

if __name__ == "__main__":
    main() 
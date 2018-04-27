import sys
import ijson
import simplejson as json
from pathlib import Path

counties = ['carlow', 'cavan', 'clare', 'cork', 'donegal', 'dublin', 'galway', 'kerry', 'kildare', 'kilkenny', 'laois',
            'leitrim', 'limerick', 'longford', 'louth', 'mayo', 'meath', 'monaghan', 'offaly', 'roscommon', 'sligo',
            'tipperary', 'waterford', 'westmeath', 'wexford', 'wicklow']

json_file_path = ''
json_file = None
json_data = None
total_number_of_townlands = 61098  # From Wikipedia


def write_progress(count, total=total_number_of_townlands, text=''):
    bar_len = 50  # one notch for every 2%
    filled_length = int(round(bar_len * count / float(total)))

    percent_complete = round(100.0 * count / float(total), 1)
    bar_text = '=' * filled_length + '-' * (bar_len - filled_length)

    # Clear previous line
    sys.stdout.write('[%s] %s%s %s\r' % (bar_text, percent_complete, '%', text))
    sys.stdout.flush()


def get_menu_choice():
    print("\n\nChoose an option from the menu")
    print(41 * '=')
    print("1. View list of townlands by county")
    print("2. Extract townlands by county")
    print("3. Convert geoJSON to GPX")
    print("4. Extract all counties' townlands into separate files")
    print("5. Exit")

    return input("> ")


def get_process_name(menu_choice):
    return {
        '1': 'list-townlands-in-county',
        '2': 'extract-townlands-in-county',
        '3': 'not-ready',
        '4': 'extract-townlands-in-all-counties',
        '5': 'exit',
    }.get(menu_choice, None)


def start_exit_process():
    if input("Are you sure? (y/n)\n> ") == 'y':
        print("Goodbye")
        global json_data
        global json_file
        json_data = None
        json_file.close()
        sys.exit(0)


def load_json_file(file_path):
    try:
        global json_file
        json_file = open(file_path, encoding='utf8')
    except FileNotFoundError:
        print("That file wasn't found... Please check your file path.")
        return False
    except IsADirectoryError:
        print("Please enter a file path, not a directory path.")
        return False
    except IOError:
        print("There was some problem loading that file...")
        return False
    else:
        # Load file contents into a JSON object
        global json_data
        json_data = ijson.items(json_file, 'features.item')

        return json_data


def input_path_and_load_file():
    # Start a loop
    while True:
        path_input = input("Enter a file path or 'exit' to leave.\n> ").strip('\"')
        if path_input.upper() == 'EXIT':
            start_exit_process()
        if not load_json_file(path_input):
            continue
        else:
            print("File loaded! Have fun.")
            global json_file_path
            json_file_path = path_input
            break


def get_county_choice():
    print("List of counties:\n")
    for county in counties:
        print(county.capitalize())

    # Start a loop
    while True:
        county_input = input("Enter a county name (case insensitive)\n> ").lower().strip()
        if county_input not in counties:
            if input("Invalid input. Try again? (y/n)") != 'y':
                break
        else:
            return county_input

    return None


def print_list_of_townlands_by_county(county):
    print("Reading file. This may take a long time. Please be patient!")
    county_upper = county.upper()
    townlands = []
    json_file_iterator = load_json_file(json_file_path)

    index = 0
    for townland in json_file_iterator:
        write_progress(index, text=county_upper)
        index += 1
        if townland['properties']['COUNTY'] == county_upper:
            townlands.append(str(townland['properties']['TD_ENGLISH']).capitalize())

    townlands.sort()
    print("Townlands in " + county.capitalize())
    for townland in townlands:
        print(townland)


def round_list(coord_list, round_to=4):
    for i, coord in enumerate(coord_list):
        if type(coord) is list:
            round_list(coord, round_to=4)
        else:
            coord_list[i] = round(coord, round_to)


def clean_townland_dict(townland_dict, keep_gaeilge=False):
    # Remove unused properties
    new_properties = {
        'TD_ENGLISH': str(townland_dict['properties']['TD_ENGLISH'])
    }
    if keep_gaeilge:
        new_properties['TD_GAEILGE'] = str(townland_dict['properties']['TD_GAEILGE'])

    townland_dict['properties'] = new_properties

    # Remove some coordinate precision
    round_list(townland_dict['geometry']['coordinates'])

    return townland_dict


def extract_townlands_by_county(county, index=0, total=total_number_of_townlands):
    # To save changing to upper case in each for loop iteration
    county_upper = county.upper()
    print("Reading file. This may take a long time. Please be patient!")

    # Make up a list of townlands in the given county
    json_file_iterator = load_json_file(json_file_path)
    townlands_dict_features = []

    for townland in json_file_iterator:
        write_progress(index, total=total, text=county_upper)
        index += 1
        if townland['properties']['COUNTY'] == county_upper:
            clean_townland_dict(townland)
            townlands_dict_features.append(townland)

    # Put the new townland list into a new dictionary in the same format as original
    townlands_dict = {
        'type': 'FeatureCollection',
        'features': townlands_dict_features
    }

    # Write the dictionary to a file in JSON representation
    path = Path(json_file_path)
    new_file_path = str(path.parent) + '/townlands_' + county + '.geojson'

    with open(new_file_path, 'w') as o_file:
        json.dump(townlands_dict, o_file)


def main():
    # Start a loop
    while True:
        menu_choice = get_menu_choice()
        process_name = get_process_name(menu_choice)

        if process_name == 'not-ready':
            print("This feature isn't ready yet, sorry!")

        elif process_name == 'list-townlands-in-county':
            county = get_county_choice()
            if county is not None:
                print_list_of_townlands_by_county(county)

        elif process_name == 'extract-townlands-in-county':
            county = get_county_choice()
            if county is not None:
                extract_townlands_by_county(county)

        elif process_name == 'extract-townlands-in-all-counties':
            if input("This will take a very long time!\n(possibly hours on slower machines)\nAre you sure you want to do this? (y/n)") != 'y':
                continue

            index = 0
            for county in counties:
                index += 1
                extract_townlands_by_county(county, index=index * total_number_of_townlands,
                                            total=len(counties) * total_number_of_townlands)

        elif process_name == 'exit':
            start_exit_process()


def print_header():
    print(41 * '=')
    print("Waze UK & Ireland Community")
    print("This script extracts information from")
    print("the huge OSI townland datasets into")
    print("more manageable files.")
    print(41 * '=')
    print("Title: Townland Clipper")
    print("Version: 0.0")
    print("Author: cw1998")
    print("Date: 24/04/18")
    # TODO print("Usage: See -h or --help")
    print("Python Version: 3")
    print(41 * '=')


if __name__ == '__main__':
    print_header()
    input_path_and_load_file()
    main()

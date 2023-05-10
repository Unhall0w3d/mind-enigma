import os
import csv


def process_csv_file(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        lines = file.readlines()

    new_lines = []
    searchterm = input("What string should we match against a line for removal?: ")
    replace = input("What character should we replace with a ','?: ")

    for line in lines:
        if searchterm not in line:
            new_line = line.replace(replace, ",")
            new_lines.append(new_line)

    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        file.writelines(new_lines)


def main():
    current_directory = os.path.dirname(os.path.realpath(__file__))
    files = os.listdir(current_directory)

    for file_name in files:
        if file_name.endswith('.csv'):
            process_csv_file(os.path.join(current_directory, file_name))


if __name__ == '__main__':
    main()

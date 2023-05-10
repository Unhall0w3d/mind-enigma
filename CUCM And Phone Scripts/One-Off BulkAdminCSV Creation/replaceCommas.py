import os

# Get the current directory
directory = os.getcwd()

# Loop through every file in the directory
for filename in os.listdir(directory):
    # Check if the file is a CSV file
    if filename.endswith(".csv"):
        # Open the file and read its contents
        with open(filename, "r") as file:
            contents = file.read()

        # Replace multiple commas with a single comma
        contents = contents.replace(",,,,,,,,", ",")
        contents = contents.replace(",,,,,,,", ",")
        contents = contents.replace(",,,,,", ",")
        contents = contents.replace(",,,,", ",")
        contents = contents.replace(",,,", ",")
        contents = contents.replace(",,", ",")

        # Write the updated contents back to the file
        with open(filename, "w") as file:
            file.write(contents)
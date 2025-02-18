import csv

def getAliases(aliasFilePath):
    """
    Reads a CSV file containing key-value pairs and returns a dictionary.

    Args:
        aliasFilePath: The path to the CSV file.

    Returns:
        A dictionary where keys are the first values in each row of the CSV,
        and values are the second values. Returns an empty dictionary if the file
        is empty or if there's an error.  Prints an error message to the console
        if an error occurs.
    """
    aliases = {}
    try:
        with open(aliasFilePath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:  # Ensure each row has exactly two values
                    key = row[0].strip()  # Remove leading/trailing whitespace
                    value = row[1].strip()
                    aliases[key] = value
                elif row: # checks if the row is not empty
                    print(f"WARN: Skipping row with incorrect number of values: {row}")
    except FileNotFoundError:
        print(f"WARN: Alias file not found at {aliasFilePath}")
    except csv.Error as e: # catch csv related errors
        print(f"WARN: Error reading CSV: {e}")
    except Exception as e: # catch other errors
        print(f"WARN: An unexpected error occurred: {e}")
    return aliases

if __name__ == "__main__":
    alias_file = "aliases.csv"  
    alias_dict = getAliases(alias_file)

    if alias_dict:
        print("Aliases:")
        for key, value in alias_dict.items():
            print(f"{key}: {value}")
    else:
        print("FATAL: No aliases found or an error occurred.")
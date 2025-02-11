import sys
import os
import xirr_filter_multiple as xirr_f

# Specify the pattern for your CSV files (replace with your pattern)
allowed_modes = ['xirr', 'trade_history']
def parseCommandLine(args):
    """
    """
    tradebook_directory = sys.argv[1]
    if not isDirectory(tradebook_directory):
        return
    mode: str = 'xirr'
    target_stock : str = None
    if len(sys.argv) > 2:
        mode = sys.argv[2]
        if not isValidMode(mode):
            allowed_modes_formatted = format_with_pipe(allowed_modes)
            print(f'FATAL: mode should be one of {allowed_modes_formatted}')
            return
    if mode == 'trade_history':
        target_stock = sys.argv[3]

    xirr_f.my_main(tradebook_directory, mode, target_stock)

def isDirectory(path):
    if not os.path.exists(path):
        print(f"FATAL: Path '{path}' does not exist.")
        return False

    if not os.path.isdir(path):
        print(f"FATAL: Path '{path}' is not a directory.")
        return False

    return True

def isValidMode(mode):
    return mode in allowed_modes

def format_with_pipe(list):
    """Formats a list of elements as "[ element1 | element2 | ... ]".
    Args: list: The list to format.

    Returns: A string representing the formatted list, or an empty string if the list is empty.
    """
    if not list:
        return '[]'

    formatted_string = '[ ' + ' | '.join(map(str, list)) + ' ]'
    return formatted_string

def getInputFromUser():
    """
    """
    tradebook_directory = input("> Enter relative or absolute path of directory containing tradebooks: ")
    if not isDirectory(tradebook_directory):
        return
    allowed_modes_formatted = format_with_pipe(allowed_modes)
    mode = input(f'> Enter mode {allowed_modes_formatted}: ')
    if not isValidMode(mode):
        print(f'FATAL: mode should be one of {allowed_modes_formatted}')
        return
    xirr_f.my_main(tradebook_directory, mode, None)

if __name__ == "__main__":  # This ensures the code only runs when the script is executed directly
    if len(sys.argv) > 1:
        print('Running in non-interactive mode ...')
        parseCommandLine(sys.argv)
    else:
        print("No command line arguments specified, running in interactive mode")
        getInputFromUser()
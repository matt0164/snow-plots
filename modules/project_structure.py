import os

# List of files and directories to be ignored
IGNORED_NAMES = {".DS_Store", ".git", ".idea", ".vscode", "__pycache__", ".venv", "env", "venv"}


def generate_directory_structure(directory):
    """
    Walks through the given directory and returns the hierarchical structure as a string.
    System files and specified directories are ignored.
    """
    structure = []
    for root, dirs, files in os.walk(directory):
        # Filter out ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_NAMES]

        # Add the current directory to the structure
        level = root.replace(directory, '').count(os.sep)
        indent = '│   ' * level + '├── '
        structure.append(f"{indent}{os.path.basename(root)}/")

        # Add all non-ignored files in this directory
        sub_indent = '│   ' * (level + 1) + '├── '
        for file in files:
            if file not in IGNORED_NAMES:
                structure.append(f"{sub_indent}{file}")

    return "\n".join(structure)


def write_project_structure(root_directory, output_file):
    """
    Writes the directory structure of the given root_directory to the output_file.
    """
    # Generate the directory structure as a string (filtered)
    structure = generate_directory_structure(root_directory)

    # Write the structure to the output file using UTF-8 encoding to support special characters
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(structure)


def main():
    """
    Main function that calculates the root directory and generates a cleaned project_structure.txt file.
    """
    # Get the absolute path to the project root ('snow-plots')
    current_file_path = os.path.abspath(__file__)  # Current script's location
    project_root = os.path.dirname(os.path.dirname(current_file_path))  # Navigate up to project root

    # Define the output file path
    output_file = os.path.join(project_root, 'project_structure.txt')

    # Generate and write the project structure to project_structure.txt
    write_project_structure(project_root, output_file)
    print(f"Cleaned project structure has been written to {output_file}")


# Entry point of the program
if __name__ == "__main__":
    main()

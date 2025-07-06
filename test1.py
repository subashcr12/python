import subprocess

def get_last_modified_file():
    try:
        # Get the last modified file tracked by Git
        file = subprocess.check_output(
            ['git', 'log', '-1', '--name-only', '--pretty=format:'],
            text=True
        ).strip()
        if not file:
            print("No recently modified file found.")
            return None
        return file
    except subprocess.CalledProcessError:
        print("Error retrieving last modified file. Ensure you are in a Git repo.")
        return None

def open_in_visual_studio(file_path):
    try:
        # Use 'devenv' CLI to open the file in Visual Studio
        subprocess.run(['devenv', file_path])
        print(f"Opening {file_path} in Visual Studio...")
    except FileNotFoundError:
        print("Visual Studio 'devenv' CLI not found. Ensure it's in your PATH.")

if __name__ == "__main__":
    last_file = get_last_modified_file()
    if last_file:
        open_in_visual_studio(last_file)

#sample
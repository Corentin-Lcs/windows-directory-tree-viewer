import os
import sys
import stat
import ctypes

# Directories to exclude from scanning.
EXCLUDED_DIRECTORIES = ['System Volume Information', 'System']

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Attempt to relaunch the script with administrative privileges if not already running as admin."""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()

def get_storage_devices():
    """Retrieve the list of storage devices available on the system."""
    drives = []
    for drive in os.popen("wmic logicaldisk get caption").read().split()[1:]:
        drives.append(drive)
    return drives

def is_hidden_or_system_protected(directory):
    """
    Check if a directory is hidden or system protected.

    Parameters:
    directory (str): Directory path to check.

    Returns:
    bool: True if the directory is hidden or system protected, False otherwise.
    """
    attributes = os.stat(directory).st_file_attributes
    return (attributes & stat.FILE_ATTRIBUTE_HIDDEN) or (attributes & stat.FILE_ATTRIBUTE_SYSTEM)

def get_drive_name(drive_letter):
    """
    Retrieve the volume label for a given drive letter.

    Parameters:
    drive_letter (str): Drive letter (e.g., 'C').

    Returns:
    str: Volume label of the drive.
    """
    if drive_letter == 'C':
        return 'Local Disk'
    volume_info = ctypes.create_unicode_buffer(256)
    ctypes.windll.kernel32.GetVolumeInformationW(drive_letter + ":\\", volume_info, 256, None, None, None, None, 0)
    return volume_info.value.strip()

def display_tree_structure(path, prefix="", file_obj=None):
    """
    Display the directory tree structure starting from a given path.

    Parameters:
    path (str): Directory path to start from.
    prefix (str, optional): Prefix to prepend to each line for visual hierarchy.
    file_obj (file object, optional): File object to write the tree structure to.

    Notes:
    If file_obj is None, the tree structure is displayed in the terminal.
    """
    if file_obj is None:
        file_obj = sys.stdout
    files = []
    dirs = []
    try:
        for entry in os.scandir(path):
            if entry.is_dir() and not is_hidden_or_system_protected(entry.path):
                dirs.append((entry.name, entry.path))
            elif not entry.is_symlink() and not is_hidden_or_system_protected(entry.path):
                files.append(entry.name)
    except PermissionError:
        print(f"'{path}': Permission denied. Skipping.")
        return
    if dirs:
        last_index = len(dirs) - 1
        for index, (name, directory) in enumerate(dirs):
            new_prefix = prefix + ("│   " if index < last_index else "    ")
            if index == last_index:
                print(prefix + "└── " + name + '/', file=file_obj)
            else:
                print(prefix + "├── " + name + '/', file=file_obj)
            display_tree_structure(directory, new_prefix, file_obj)
    for index, file in enumerate(files):
        if index == len(files) - 1 and not dirs:
            print(prefix + "└── " + file, file=file_obj)
        else:
            print(prefix + "├── " + file, file=file_obj)

def save_tree_to_file(selected_device):
    """
    Save the directory tree structure of a selected device to a file.

    Parameters:
    selected_device (str): Selected device path (e.g., 'C:\\') to generate the tree structure from.
    """
    filename = input("Enter the filename to save the tree view: ") + ".txt"
    with open(filename, 'w', encoding='utf-8') as f:
        display_tree_structure(selected_device + "\\", "", f)
    
def main():
    """Main function to execute the program."""
    run_as_admin()
    devices = get_storage_devices()
    print("|------------------------------[ Windows Directory Tree Viewer ]------------------------------|")
    print("\nStorage devices:\n")
    for index, device in enumerate(devices, 1):
        drive_letter = device.strip(":")
        drive_name = get_drive_name(drive_letter)
        print(f"{index}. {drive_name} ({device})")
    try:
        choice_index = int(input("\nSelect a storage device (enter the number): ")) - 1
        selected_device = devices[choice_index]
        display_option = input("Display in terminal (T) or write to file (F) ? ").upper()
        if display_option == 'T':
            display_tree_structure(selected_device + "\\")
            save_to_file = input("\nDo you want to save the tree view to a file ? (Y/N) ").upper()
            if save_to_file == 'Y':
                save_tree_to_file(selected_device)
        elif display_option == 'F':
            save_tree_to_file(selected_device)
        else:
            print("Invalid option selected. Tree view not saved.\n")
    except (IndexError, ValueError):
        print("Invalid choice or device.\n")

if __name__ == "__main__":
    main()
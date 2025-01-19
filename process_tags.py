import dropbox
from dropbox.exceptions import ApiError
import glob
from io import BytesIO
import macos_tags
import os
import pandas as pd
from tkinter import Tk, filedialog
import tkinter.simpledialog as simpledialog

def select_folder(title):
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    folder_path = filedialog.askdirectory(title=title)
    root.destroy()
    return folder_path

def get_finder_tags(folder):
    files_list = glob.glob(f"{folder}/*.[Jj][Pp][Gg]")
    return {os.path.basename(picture): [tag.name for tag in macos_tags.get_all(picture)] for picture in files_list}

def create_dropbox_folder(dbx, path):
    try:
        dbx.files_create_folder(path=path)
        print("Folder created successfully.")
    except ApiError as e:
        if (isinstance(e.error, dropbox.files.CreateFolderError) and 
                e.error.get_path().is_conflict()):
            print("The folder already exists.")
        else:
            raise

def upload_file(dbx, local_path, remote_path):
    try:
        dbx.files_get_metadata(remote_path)
        print(f"{os.path.basename(local_path)} already exists. Skipping upload.")
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            with open(local_path, 'rb') as f:
                dbx.files_upload(f.read(), remote_path)
                print(f"Uploaded {os.path.basename(local_path)}")
        else:
            raise

def add_tags_to_file(dbx, file_path, tags):
    for tag in tags:
        truncated_tag = tag.replace(" ", "_")[:32]
        print(f"Adding tag '{truncated_tag}' to {file_path}")
        dbx.files_tags_add(path=file_path, tag_text=truncated_tag)

def generate_and_upload_excel(dbx, tags_dict, dropbox_path):
    data = [(file, tag.replace(" ", "_")[:32]) for file, tags in tags_dict.items() for tag in tags]
    df_tags_map = pd.DataFrame(data, columns=['File', 'Tag'])

    buffer = BytesIO()
    df_tags_map.to_excel(buffer, index=False, engine='xlsxwriter')
    buffer.seek(0)

    excel_path = f"{dropbox_path}/tags.xlsx"
    dbx.files_upload(buffer.read(), excel_path)
    print(f"Tags Excel file uploaded to {excel_path}")

def main():
    # Select local folder
    local_folder = select_folder("Select the folder containing images")
    if not local_folder:
        print("No folder selected. Exiting.")
        return

    # Select Dropbox folder path
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    dropbox_path = simpledialog.askstring("Dropbox Path", "Enter the Dropbox folder path")
    root.destroy()
    
    if not dropbox_path:
        print("No Dropbox path entered. Exiting.")
        return

    # Enter Dropbox API key
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    dropbox_key = simpledialog.askstring("Dropbox API Key", "Enter your Dropbox API key")
    root.destroy()
    if not dropbox_key:
        print("No Dropbox API key entered. Exiting.")
        return

    # Initialize Dropbox
    dbx = dropbox.Dropbox(dropbox_key)

    # Extract Finder tags
    tags_dict = get_finder_tags(local_folder)

    # Create Dropbox folder
    create_dropbox_folder(dbx, dropbox_path)

    # Upload files and add tags
    for file, tags in tags_dict.items():
        local_file_path = os.path.join(local_folder, file)
        remote_file_path = f"{dropbox_path}/{file}"
        upload_file(dbx, local_file_path, remote_file_path)
        add_tags_to_file(dbx, remote_file_path, tags)

    # Generate and upload Excel with tag mappings
    generate_and_upload_excel(dbx, tags_dict, dropbox_path)

if __name__ == "__main__":
    main()

import dropbox
from dropbox.exceptions import ApiError
import glob
from io import BytesIO
import macos_tags
import os
import pandas as pd
from PIL import Image, ImageTk
from tkinter import Tk, filedialog, Toplevel, Button, Scrollbar, ttk, Label
import tkinter.simpledialog as simpledialog
import re
import unicodedata

import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for development and PyInstaller """
    if hasattr(sys, '_MEIPASS'):  # PyInstaller temp directory
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Update image paths:
image1_path = get_resource_path("images/step1.jpg")
image2_path = get_resource_path("images/step2.jpg")
image3_path = get_resource_path("images/step3.jpg")



def show_image_window(image_path, message):
    """Display a window with a message and an image, resizing the image to a fixed width while maintaining its aspect ratio."""
    window = Toplevel()
    window.title("Step 1")

    # Load image using PIL
    img = Image.open(image_path)

    # Calculate the new image dimensions to maintain aspect ratio
    fixed_width = 800
    aspect_ratio = img.height / img.width
    new_height = int(fixed_width * aspect_ratio)  # Compute height based on aspect ratio
    img = img.resize((fixed_width, new_height))  # Resize image

    img_tk = ImageTk.PhotoImage(img)

    # Adjust the window's size to fit the image size with padding for message and button
    window.geometry(f"{fixed_width + 20}x{new_height + 120}")  # Add extra pixels for message/button

    # Display the message above the image
    message_label = Label(window, text=message, font=("Arial", 14), wraplength=fixed_width, justify="center")
    message_label.pack(pady=10)

    # Display the image
    label = Label(window, image=img_tk)
    label.image = img_tk  # Keep a reference to avoid garbage collection
    label.pack()

    # Add a button to close the window and proceed
    Button(window, text="Continue", command=window.destroy).pack(pady=10)

    # Wait for the window to be closed
    window.wait_window()
   



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
            
def normalize_tag(tag):
    # Remove accents and normalize to ASCII
    normalized_tag = ''.join(
        c for c in unicodedata.normalize('NFD', tag)
        if unicodedata.category(c) != 'Mn'
    )
    # Replace invalid characters with underscores and truncate to 32 characters
    sanitized_tag = re.sub(r'[^a-zA-Z0-9_]', '_', normalized_tag)[:32]
    return sanitized_tag

def add_tags_to_file(dbx, file_path, tags):
    for tag in tags:
        sanitized_tag = normalize_tag(tag)
        print(f"Adding sanitized tag '{sanitized_tag}' from  '{tag}' to {file_path}")
        try:
            dbx.files_tags_add(path=file_path, tag_text=sanitized_tag)
        except Exception as e:
            print(f"Failed to add tag '{sanitized_tag}' to {file_path}: {e}")

def generate_and_upload_excel(dbx, tags_dict, dropbox_path):
    data = [(tag, "#"+normalize_tag(tag)) for _, tags in tags_dict.items() for tag in tags]
    
    # Create DataFrame
    df_tags_map = pd.DataFrame(data, columns=['jugador', 'tag'])
    
    # Remove duplicates
    df_tags_map = df_tags_map.drop_duplicates(subset=['tag']).copy()
    
    # Sort by 'jugador'
    df_tags_map = df_tags_map.sort_values(by='jugador').reset_index(drop=True)
    

    buffer = BytesIO()
    df_tags_map.to_excel(buffer, index=False, engine='xlsxwriter')
    buffer.seek(0)

    excel_path = f"{dropbox_path}/tags.xlsx"

    try:
        # Check if the file exists
        try:
            dbx.files_get_metadata(excel_path)
            print(f"File {excel_path} already exists. Deleting it.")
            dbx.files_delete_v2(excel_path)
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path() and e.error.get_path().is_not_found():
                print(f"File {excel_path} does not exist. Proceeding to create it.")
            else:
                raise  # Re-raise other exceptions

        # Upload the new file
        dbx.files_upload(buffer.read(), excel_path)
        print(f"Tags Excel file uploaded to {excel_path}")

    except dropbox.exceptions.ApiError as e:
        print(f"Error handling the Excel file: {e}")



def get_dropbox_folder_structure(dbx, path=""):
    """Recursively fetch Dropbox folder structure."""
    try:
        folder_structure = dbx.files_list_folder(path)
        return {entry.name: entry for entry in folder_structure.entries}
    except ApiError as e:
        print(f"Error fetching Dropbox folder structure: {e}")
        return {}

def select_dropbox_folder(dbx):
    """Show a folder selection dialog with the ability to explore and select subdirectories in Dropbox."""
    selected_folder = None  # Define the variable to store the selected folder

    def populate_tree(parent, path):
        """Populate the tree view with folder contents."""
        try:
            folder_structure = get_dropbox_folder_structure(dbx, path)
            for name, entry in folder_structure.items():
                if isinstance(entry, dropbox.files.FolderMetadata):
                    node_id = tree.insert(parent, 'end', text=name, values=(entry.path_lower,))
                    # Add a dummy child to allow expanding
                    tree.insert(node_id, 'end')
        except Exception as e:
            print(f"Error fetching folder contents: {e}")

    def on_open(event):
        """Handle expanding a folder to load its contents."""
        selected_item = tree.focus()
        folder_path = tree.item(selected_item, 'values')[0]

        # Check if the folder is already populated
        if tree.get_children(selected_item):
            # If there are already children, don't reload
            if len(tree.get_children(selected_item)) == 1:
                # If there's only a dummy child, populate the folder
                tree.delete(tree.get_children(selected_item)[0])
                populate_tree(selected_item, folder_path)

    def on_select():
        """Set the selected folder and close the dialog."""
        nonlocal selected_folder
        selected_item = tree.focus()
        selected_folder = tree.item(selected_item, 'values')[0]
        dialog.destroy()

    # Fetch root folder structure
    root_structure = get_dropbox_folder_structure(dbx, "")

    # Create Tkinter dialog
    dialog = Toplevel()
    dialog.title("Select Dropbox Folder")
    dialog.geometry("500x400")

    # Treeview for folder structure
    tree = ttk.Treeview(dialog)
    tree.heading('#0', text='Dropbox Folders', anchor='w')
    tree.column('#0', stretch=True)

    # Populate the root folders
    populate_tree('', '')

    # Bind expand event
    tree.bind('<<TreeviewOpen>>', on_open)

    # Scrollbar
    scrollbar = Scrollbar(dialog, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    tree.pack(fill="both", expand=True)

    # Select button
    Button(dialog, text="Select", command=on_select).pack(pady=5)

    dialog.wait_window()
    return selected_folder


def main():
    # Select local folder
    local_folder = select_folder("Select the folder containing images")
    if not local_folder:
        print("No folder selected. Exiting.")
        return
    
    # Instructions 
    show_image_window(image1_path, "Go to the link: https://www.dropbox.com/developers/apps and click the existing app")
    show_image_window(image2_path, "Scroll down and Click on the 'Generate' button under Generate access token to generate an access token")
    show_image_window(image3_path, "Copy the generated access token and paste it in the dialog box that will appear next")

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

    # Select Dropbox folder path
    dropbox_path = select_dropbox_folder(dbx)
    if not dropbox_path:
        print("No Dropbox path selected. Exiting.")
        return

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

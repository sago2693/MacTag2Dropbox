# MacTag2Dropbox

MacTag2Dropbox is a Python script that reads Finder tags from photos on macOS and uploads the photos to Dropbox, preserving their tags in Dropbox's format. It also generates an Excel file summarizing the tags for easy reference.

## Features

- Extracts Finder tags from image files in a specified folder.
- Uploads photos to a specified Dropbox folder.
- Maps Finder tags to Dropbox-compatible tags, truncating where necessary.
- Generates an Excel file with the original and truncated tags for documentation.
- Handles existing files in Dropbox gracefully (avoids re-uploading).

## Prerequisites

- macOS with Python 3.x installed.
- Dropbox account and API key.

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/sago2693/MacTag2Dropbox.git
    cd MacTag2Dropbox
    ```

2. Install the required Python libraries:
    ```bash
    pip install macos-tags dropbox pandas openpyxl xlsxwriter
    ```

## Configuration

1. Prepare the local folder containing the image files and ensure each file has Finder tags applied.

2. Update the script with the following variables:
   - `folder`: Local folder containing image files.
   - `DROPBOX_PATH`: Dropbox folder path where photos will be uploaded.
   - `dropboxkey`: Your Dropbox API key.

## Usage

1. Run the script:
    ```bash
    python MacTag2Dropbox.py
    ```

2. The script will:
   - Extract Finder tags from the specified local folder.
   - Create the target Dropbox folder if it doesn't already exist.
   - Upload the photos, skipping files that already exist.
   - Map Finder tags to Dropbox-compatible tags (truncated to 32 characters if necessary).
   - Generate and upload an Excel file (`tags.xlsx`) containing the tag mappings.

## Script Overview

### Extract Finder Tags
The script uses the `macos-tags` library to read Finder tags from the specified folder:
```python
import macos_tags
...
tags_list = macos_tags.get_all(picture)
```

### Upload Photos to Dropbox
The script checks for existing files to avoid duplicate uploads:
```python
try:
    dbx.files_get_metadata(remote_file_path)
    print(f"{file} already exists. Skipping upload.")
except dropbox.exceptions.ApiError as e:
    ...
```

### Map Tags to Dropbox
Tags are truncated to fit Dropbox's 32-character limit and added to uploaded files:
```python
truncated_tag = tag.replace(" ", "_")[:32]
dbx.files_tags_add(path=remote_file_path, tag_text=truncated_tag)
```

### Generate Excel Report
An Excel file mapping original and truncated tags is generated and uploaded:
```python
buffer = BytesIO()
df_tags_map.to_excel(buffer, index=False, engine='xlsxwriter')
dbx.files_upload(buffer.read(), f'{DROPBOX_PATH}/tags.xlsx')
```

## Error Handling
The script gracefully handles errors, including:
- Skipping existing Dropbox files.
- Handling Dropbox folder creation conflicts.
- Reporting API and permission errors.

## Limitations
- Dropbox tags are limited to 32 characters, so tags longer than this are truncated.
- Finder tags are only supported on macOS.

## Contributions
Contributions are welcome! Feel free to submit a pull request or open an issue if you encounter any problems.

## License
This project is licensed under the MIT License. See the LICENSE file for details.


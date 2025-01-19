# MacTag2Dropbox

MacTag2Dropbox is a Python script that reads **Finder** tags from photos on macOS and uploads the photos to Dropbox, preserving their tags in Dropbox's format. It also generates an Excel file summarizing the tags for easy reference.

## Features

- Extracts Finder tags from image files in a specified folder.
- Uploads photos to a specified Dropbox folder.
- Maps Finder tags to Dropbox-compatible tags, truncating where necessary given dropbox's restrictions on tags.
- Generates an Excel file with the original and truncated tags to use for searching in dropbox
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
2. Install the conda environment:
    ```bash
    conda env create -f environment.yml
    conda activate tag-dbx-env
    ```
3. Install python dependencies with poetry:
    ```bash
    poetry config virtualenvs.create false
    poetry install
    ```


## Configuration

1. Prepare the local folder containing the image files and ensure that the images are adequately tagged in Finder.

2. Create a Dropbox app and generate an access token:
    - Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps).
    - Click on "Create app" and select "Scoped access".
    - Choose the "App folder" option and give your app a name.
    - Generate an access token under the "OAuth 2" section.

3. The dialogue box will ask for the following information:
    - **Local folder path**: The path to the folder containing the image files.
    - **Dropbox access token**: The access token generated in step 2.
    - **Dropbox folder path**: The path to the Dropbox folder where the images will be uploaded.

## Usage

1. Run the script:
    ```bash
    python process_tags.py
    ```

2. The script will:
   - Extract Finder tags from the specified local folder.
   - Create the target Dropbox folder if it doesn't already exist.
   - Upload the photos, skipping files that already exist.
   - Map Finder tags to Dropbox-compatible tags (truncated to 32 characters if necessary).
   - Generate and upload an Excel file (`tags.xlsx`) containing the tag mappings.


## Contributions
Contributions are welcome! Feel free to submit a pull request or open an issue if you encounter any problems.

## License
This project is licensed under the MIT License. See the LICENSE file for details.


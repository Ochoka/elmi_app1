# Data Handling and QA Application

This Streamlit application enables authenticated users to download, format, and edit data for verification purposes. It provides an interface to access and manage datasets from Kobo for Key Informant Interviews (KII)/Survey and Focus Group Discussions (FGD). Users can view or edit the data directly within the app and download the edited data in Excel format.

## Features

- **User Authentication**: Secure login with `streamlit_authenticator`.
- **Data Access**: Access and select data by type (KII/Survey or FGD) using a drop-down menu.
- **Data Viewing**: View raw data in the app with the option to download it as an Excel file.
- **Data Editing**: Edit data inline within the app. Changes can be saved and downloaded.
- **Download Functionality**: Download the original or edited data as an Excel file.
- **Dynamic Styling**: Customized interface with background colors to distinguish main and sidebar areas.

## Installation

### Prerequisites
- Python 3.8 or higher
- Streamlit, PyYAML, pickle, and other dependencies as listed below.

### Dependencies
Install the necessary packages:
```bash
pip install streamlit kobo_access pickle pyyaml streamlit_authenticator
```
### Configuration
Set up a ```config.yaml``` file to store user credentials and cookie information for user authentication.

Sample ```config.yaml```:

```bash
credentials:
  - username: "user1"
    password: "hashed_password"
cookie:
  name: "your_cookie_name"
  key: "your_cookie_key"
  expiry_days: 30

```
### Usage

1. Run the application:
```bash
streamlit run elmi_app1.py

```
2. Log in with the credentials provided in ```config.yaml```. 
3. Select the data type (KII/Survey or FGD) from the sidebar and choose a specific verification dataset. 
4. Choose an action (View or Review) to either view the data or make edits. 
5. Download the data as an Excel file from the sidebar.

### File Structure
- **app.py**: Main application file with Streamlit code.
- **config.yaml**: Configuration file for authentication.
- **kobo_access.py**: Module for data extraction and manipulation with Kobo API.
- **assets/**: Folder for any static files (optional).

### Modules
- **kobo_access**: Contains functions to extract and manipulate data from Kobo, including functions to create downloadable Excel files and edit data.
- **streamlit_authenticator**: Manages user authentication for secure access.

### Security
- **User Authentication**: Uses ```streamlit_authenticator``` to restrict access to authenticated users only.
- **Password Hashing**: Ensure passwords are hashed in ```config.yaml``` to prevent exposure of plain text credentials.

### Known Issues
- **Session Management**: Some users may experience issues with session persistence; ensure the ```cookie``` settings in ```config.yaml``` are correctly configured.



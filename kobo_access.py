from koboextractor import KoboExtractor
import streamlit as st
import pandas as pd
import re
import base64
from io import BytesIO
import numpy as np
import xlsxwriter

# Store the extraction information
KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
url = 'https://kf.kobotoolbox.org/api/v2'

# Initiate the KoboExtractor
kobo = KoboExtractor(KOBO_TOKEN, url)


def initialize_kobo_extractor():
    # Initiate the KoboExtractor
    kobo = KoboExtractor(KOBO_TOKEN, url)
    return kobo


# Function to encode a local image file to base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Get verifications
def extract_kobo_projects():
    # Initialize lists to store user IDs and project names
    user_ids = []
    project_names = []

    # Retrieve assets and extract information
    assets = kobo.list_assets()
    for asset in assets['results']:
        user_ids.append(asset['uid'])
        project_names.append(asset['name'])

    return user_ids, project_names


def get_kii_data(user_uid, kobo=kobo):
    # Retrieve asset, choices, and questions from Kobo API
    asset = kobo.get_asset(user_uid)
    choice_lists = kobo.get_choices(asset)
    questions = kobo.get_questions(asset=asset, unpack_multiples=True)

    # Fetch the data
    new_data = kobo.get_data(user_uid)

    # Check if data is available
    if new_data['results']:
        # Sort results by time and label each result
        new_results = kobo.sort_results_by_time(new_data['results'])
        labeled_results = [
            kobo.label_result(
                unlabeled_result=result,
                choice_lists=choice_lists,
                questions=questions,
                unpack_multiples=True
            )
            for result in new_results
        ]

        # List to store combined rows for each entry
        combined_rows = []

        # Process each labeled result
        for entry in labeled_results:
            # Extract meta data
            meta_data = {
                'start': entry['meta']['start'],
                'end': entry['meta']['end'],
                'Latitude': entry['meta']['_geolocation'][0],
                'Longitude': entry['meta']['_geolocation'][1]
            }

            # Extract labeled result data
            result_data = {
                value['label']: value['answer_label']
                for key, value in entry['results'].items()
            }

            # Combine meta data and result data
            combined_data = {**meta_data, **result_data}
            combined_rows.append(combined_data)

        # Convert combined rows to a DataFrame
        df = pd.DataFrame(combined_rows)

        # Remove columns starting with "Time difference in"
        df = df.loc[:, ~df.columns.str.startswith("Time difference in")]
        return df
    else:
        return None


# FGD functions
def extract_list_names(data):
    result = {}
    def traverse(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and 'list_name' in value:
                    result[key] = value['list_name']
                traverse(value)
        elif isinstance(data, list):
            for item in data:
                traverse(item)
    traverse(data)
    return result

def extract_and_clean_labels(data):
    result = {}
    def traverse(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and 'label' in value:
                    cleaned_label = re.sub(
                        r'\s*\$\{.*?\}.*', '',
                        value['label']).split('\n')[0].strip()
                    result[key] = cleaned_label
                traverse(value)
        elif isinstance(data, list):
            for item in data:
                traverse(item)
    traverse(data)
    return result


# Create a downloadable xlsx file
def create_excel_file(df, sheet_name='Sheet1'):
    sheet_name = sheet_name[:31]
    # Create an Excel file in memory
    output = BytesIO()

    # Use XlsxWriter as the engine to apply formatting
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        # Access the XlsxWriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Define a format with text wrapping and borders
        wrap_border_format = workbook.add_format({
            'text_wrap': True,
            'border': 1  # Adds a border around cells
        })

        # Set a fixed column width (e.g., 20) for each column
        if len(df.columns) >= 4:
            fixed_width = 20
        else:
            fixed_width = 40
        for col_num, _ in enumerate(df.columns):
            worksheet.set_column(col_num, col_num, fixed_width)

        # Apply the wrap and border format only to cells containing data
        for row in range(len(df)):
            for col in range(len(df.columns)):
                cell_value = df.iloc[row, col]
                # Check if cell_value is NaN or INF and only use np.isinf() for numbers
                if pd.isna(cell_value) or (isinstance(cell_value, (int, float)) and np.isinf(cell_value)):
                    worksheet.write(row + 1, col, '', wrap_border_format)  # Write empty cell for NaN/INF
                else:
                    worksheet.write(row + 1, col, cell_value, wrap_border_format)  # Adjust for header row

    output.seek(0)  # Move the cursor back to the beginning of the file

    return output

# Make edits on dataframe
def editable_dataframe(df):
    # Display an editable DataFrame
    edited_df = st.data_editor(df, num_rows="dynamic", hide_index=True,
                               use_container_width=True, width=2000)

    # Add a button to commit changes
    if st.sidebar.button("Commit Changes"):
        # Create a new DataFrame with the edits
        new_df = edited_df.copy()
        st.sidebar.success("Changes committed successfully!")
        return new_df
    else:
        return None  # Return None if changes aren't committed


def generate_dataframes(user_id):
    # Fetch data using kobo API methods
    data = kobo.get_data(user_id)

    # Check if data is empty and return an empty list if so
    if not data or 'results' not in data or not data['results']:
        return []  # Return an empty list if data is empty or has no results

    asset = kobo.get_asset(user_id)
    choice_lists = kobo.get_choices(asset)
    questions = kobo.get_questions(asset=asset, unpack_multiples=True)

    # Initialize an empty dictionary to store each df created with dynamic names
    df_lists = {}

    # Loop through data['results'] to get the data
    for index, entry in enumerate(data['results']):
        # Get the data for individual verification
        data1 = data['results'][index]
        # Filter the data based on dictionary
        filtered_dict = {key: value for key, value in data1.items()
                         if isinstance(value, list) and
                         any(isinstance(i, dict) for i in value)}

        # Initialize an empty list to store each DataFrame created in the loop
        df_list = []

        # Loop through and create the DataFrame
        for i in filtered_dict:
            # Create DataFrame by normalizing JSON data
            df2 = pd.json_normalize(filtered_dict[i])

            # Drop columns that end with '_index'
            df2 = df2[df2.columns.drop(list(df2.filter(regex='_index$')))]

            # Append df2 to the list
            df_list.append(df2)
        df1 = pd.concat(df_list, axis=1)

        # Get the number of rows of the DataFrame
        nrows = df1.shape[0]

        # Get and append the latitudes and longitudes in the df
        precise_location = entry.get(
            'consented_grp/section_b/precise_location')
        if precise_location:
            location_parts = precise_location.split()
        lat = [location_parts[0] for _ in range(nrows)]
        lon = [location_parts[1] for _ in range(nrows)]

        # Add the latitudes and longitudes
        df1.insert(0, 'Longitude', lon)
        df1.insert(0, 'Latitude', lat)

        # Get start and end dates
        start_dates = [entry.get('start') for _ in range(nrows)]
        end_dates = [entry.get('end') for _ in range(nrows)]

        # Add the start and end dates
        df1.insert(0, 'End', end_dates)
        df1.insert(0, 'Start', start_dates)

        # Clean the columns
        cols = [col for col in df1.columns if
                col.startswith('consented_grp')]

        # Extract the third value from each string if it has at least three parts
        fourth_values = [item.split('/')[-1] for item in cols]

        columns_cleaned = ['start', 'end', 'Latitude', 'Longitude']
        for i in fourth_values:
            columns_cleaned.append(i)

        # Rename columns for df
        df1.columns = columns_cleaned

        # Get questions
        questions1 = questions['groups']['consented_grp']['groups']
        list_name_labels = extract_list_names(questions1)

        # Iterate over the list_name_keys to modify the appropriate columns in df
        for col, list_name in list_name_labels.items():
            if col in df1.columns and list_name in choice_lists:
                # Replace the numeric values in the column with the
                # corresponding labels from choice_lists
                df1[col] = df1[col].astype(str).map(
                    lambda x: choice_lists[list_name].get(x, {}).get(
                        'label', x))

        questions2 = extract_and_clean_labels(questions1)
        questions2 = {key: value for key, value in questions2.items() if
                      'section_' not in key}
        filtered_list_name_labels = {k: v for k, v in questions2.items() if
                                     k in df1.columns}
        filtered_list_name_labels = filtered_list_name_labels.values()

        # Append the first two columns
        questions_lists = (['start', 'end', 'Latitude', 'Longitude'] +
                           list(
                               filtered_list_name_labels))

        # Transpose the data with questions in row
        df_transposed = df1.transpose()

        # Get the total number of columns in df_transposed
        total_columns = df_transposed.shape[1]

        # Create the "Respondent number" vector starting from 1 to
        # total number of columns
        respondent_number = [f"Respondent {res + 1}" for res in
                             range(total_columns)]

        df_transposed.columns = respondent_number

        # Add the questions
        df_transposed.insert(0, 'Question',
                             questions_lists)

        # Reset the row index of df_transposed without
        # creating an index column
        df_transposed.reset_index(drop=True, inplace=True)

        # Get verification number
        ver_no_select = entry.get(
            'consented_grp/section_b/verification_no')

        # Access the 'verification_no' dictionary and get the label for
        # the specified ver_no_select
        base_ver_no = choice_lists[
            'verification_no'].get(ver_no_select,
                                   {}).get('label', f"df_{index + 1}")

        # Check if ver_no already exists in df_lists,
        # add a suffix if it does
        ver_no = base_ver_no
        suffix = 1
        while ver_no in df_lists:
            ver_no = f"{base_ver_no}_{suffix}"
            suffix += 1

        # Update the df dictionary with dynamic names
        df_lists[ver_no] = df_transposed

    return df_lists



if __name__ == "__main__":
    # Test the functions
    user_id = 'agnYS6ing2xugLZansqRDj'
    # df = get_kii_data(user_uid=user_id, kobo=kobo)
    # print(df.head())
    df = generate_dataframes(user_id)
    df.keys()
    pass

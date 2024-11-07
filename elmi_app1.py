# Import needed libraries
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import kobo_access as ka

# Page configuration
st.set_page_config(page_title="Data Handling", page_icon=":bar_chart:",
                   layout="wide")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    authenticator.login()
except Exception as e:
    st.sidebar.error(e)

if st.session_state['authentication_status']:
    # Use Streamlit's markdown feature to insert HTML with inline CSS
    st.html(
        """
    <style>
    [data-testid="stSidebarContent"] {
        color: Black;
        background-color: #03fcf8;
    }

    [data-testid="stMain"] {
        color: #002A6C;
        background-color: #cce7e8;
    }

    </style>
    """
    )
    st.sidebar.write(f'Welcome **{st.session_state["name"]}**')
    # set title
    st.title("Download, Format and Edit Data")
    # Set a sidebar for selecting data to access
    data_type = st.sidebar.selectbox("Select the Data Type",
                                     ("KII/Survey", "FGD"),
                                     index=None,
                                     placeholder=
                                     "You can choose KII/Survey or FGD")

    # Start handling data
    if data_type is not None:
        # Access all projects in kobo
        user_ids, project_names = ka.extract_kobo_projects()

        # Handling KII data
        if data_type == "KII/Survey":
            # Extract KII data only and allow user to select one
            kiis = [name for name in project_names if 'kii' in name.lower() or
                    'survey' in name.lower()]

            # Let user choose a KII from the list
            kii_selected = st.sidebar.selectbox(
                f"{data_type} Verifications", kiis, index=None,
                placeholder="Choose a verification")

            # Work with the selected KII data
            if kii_selected is not None:
                # Find the index of the selected KII
                index_kii_selected = project_names.index(kii_selected)

                # Get the corresponding user ID
                user_id_kii_selected = user_ids[index_kii_selected]
                df = ka.get_kii_data(user_id_kii_selected)

                # Check for availability of data
                if df is not None:
                    #transpose the data
                    df = df.T

                    # Set first column as the index
                    df.reset_index(inplace=True)


                    # Select what to do with the file
                    action_kii = st.sidebar.selectbox("What do you want to"
                                                      " do with the data?",
                                         ("View", "Review"),
                                         index=None)
                    if action_kii is not None:
                        if action_kii == "View":
                            st.subheader(f"{kii_selected}")
                            # Remove column names
                            df.columns = [''] * len(df.columns)
                            st.markdown(df.to_html(escape=False),
                                        unsafe_allow_html=True)
                            # Create downloadable excel
                            output = ka.create_excel_file(
                                    df,
                                    sheet_name=kii_selected)

                            # Download button for the Excel file
                            st.sidebar.download_button(
                                label="Download data as Excel",
                                data=output,
                                file_name=f"{kii_selected} data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument"
                                     ".spreadsheetml.sheet"
                            )
                        if action_kii == "Review":
                            st.subheader(f"{kii_selected}")
                            edited_df = ka.editable_dataframe(df)
                            # Check if new_df has been created successfully
                            # before calling to_html
                            if edited_df is not None:
                                # Create downloadable excel
                                # Remove column names
                                edited_df.columns = [''] * len(edited_df.columns)
                                output = ka.create_excel_file(
                                    edited_df,
                                    sheet_name=kii_selected)

                                # Download button for the Excel file
                                st.sidebar.download_button(
                                    label="Download data as Excel",
                                    data=output,
                                    file_name=f"{kii_selected} Reviewed Data.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument"
                                         ".spreadsheetml.sheet"
                                )
                            else:
                                st.warning(
                                    "Please commit changes to get "
                                    "the updated DataFrame.")


                else:
                    st.write(f"No data available for {kii_selected}")
                    pass

        # Handling FGD data
        if data_type == "FGD":

            # Extract KII data only and allow user to select one
            fgds = [name for name in project_names if 'fgd' in name.lower()]

            # Let user choose a KII from the list
            fgd_selected = st.sidebar.selectbox(
                f"{data_type} Verifications", fgds, index=None,
                placeholder="Choose a Verification")

            # Get the data
            # Find the index of the selected FGD
            if fgd_selected is not None:
                index_fgd_selected = project_names.index(fgd_selected)
                user_id_selected = user_ids[index_fgd_selected]

                dfs = ka.generate_dataframes(user_id_selected)

                if dfs is not None:
                    ver_fgd = dfs.keys()

                    # Select what to do with the file
                    fgd_select1 = st.sidebar.selectbox(
                        "Select Verification",
                        ver_fgd, index=None)

                    # Select what to do with the file
                    if fgd_select1 is not None:
                        action_fgd = st.sidebar.selectbox("What do you want to"
                                                          " do with the data?",
                                                          ("View", "Review"),
                                                          index=None)
                        df = dfs[fgd_select1]

                        # Remove column names
                        if action_fgd is not None:
                            if action_fgd == "View":
                                st.subheader(f"{fgd_select1}")
                                df.columns = [''] * len(df.columns)
                                st.markdown(df.to_html(escape=False),
                                            unsafe_allow_html=True)
                                # Create downloadable excel
                                output = ka.create_excel_file(
                                    df,
                                    sheet_name=fgd_select1)

                                # Download button for the Excel file
                                st.sidebar.download_button(
                                    label="Download data as Excel",
                                    data=output,
                                    file_name=f"{fgd_select1} data.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument"
                                         ".spreadsheetml.sheet"
                                )
                            if action_fgd == "Review":
                                st.subheader(f"{fgd_select1}")
                                edited_df = ka.editable_dataframe(
                                    df,
                                    sheet_name=fgd_select1)
                                # Check if new_df has been created successfully
                                # before calling to_html
                                if edited_df is not None:
                                    # Create downloadable excel
                                    edited_df.columns = [''] * len(edited_df.columns)
                                    output = ka.create_excel_file(
                                    edited_df,
                                    sheet_name=fgd_select1)

                                    # Download button for the Excel file
                                    st.sidebar.download_button(
                                        label="Download data as Excel",
                                        data=output,
                                        file_name=f"{fgd_select1} Reviewed Data.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument"
                                             ".spreadsheetml.sheet"
                                    )
                                else:
                                    st.warning(
                                        "Please commit changes to get "
                                        "the updated DataFrame.")

                else:
                    st.write(f"No data available for {fgd_selected}")
                    pass

    authenticator.logout("Logout", "sidebar")
elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')

import streamlit as st
import pyodbc as db
import pandas as pd
import os

# Fetch the connection parameters from Streamlit secrets (or environment variables locally)
SQL_SERVER = st.secrets["sql"]["server"]
SQL_DATABASE = st.secrets["sql"]["database"]
SQL_UID = st.secrets["sql"]["user"]
#SQL_PASS = st.secrets["sql"]["password"]

# Define the driver and connection string
driver = '{ODBC Driver 17 for SQL Server}'

# Establish the connection
try:
    conn = db.connect(
        f'DRIVER={driver};'
        f'SERVER={SQL_SERVER};'  # Use Streamlit secrets for server
        f'DATABASE={SQL_DATABASE};'  # Use Streamlit secrets for database
        f'UID={SQL_UID};'  # Use Streamlit secrets for user
        #f'PWD={SQL_PASS}'  # Use Streamlit secrets for password
    )
    print("Connection established successfully")
except db.Error as e:
    st.error(f"Error connecting to database: {e}")
    st.stop()

# Set page configuration
st.set_page_config(page_title="User Search", page_icon="🦉", layout="wide")

# Password authentication for access
PASSWORD = "Jigsaw321"
password_input = st.text_input("Enter password:", type="password")

if password_input == PASSWORD:
    st.success("Authentication successful!")
else:
    if password_input != "":
        st.error("Authentication failed. Please check your credentials.")
    st.stop()

# Title of the app
st.title("Customer Search🧩")

# Input fields for postcode and school name
school_name_input = st.text_input("Enter school name to search (leave empty if not used)")
postcode_input = st.text_input("Enter postcode to search (leave empty if not used)")

# SQL query
query = """
SELECT 
    COALESCE(CONVERT(varchar(10), p1.[dateValue], 103), p1.[varcharValue], p1.[textValue], '') AS 'umbracoMemberLastLogin',
    COALESCE(p5.[varcharValue], p5.[textValue], '') AS 'schoolName',
    COALESCE(p6.[varcharValue], p6.[textValue], '') AS 'postcode'
FROM 
    [dbo].[umbracoNode] n WITH (NOLOCK)
JOIN 
    [dbo].[umbracoContent] c WITH (NOLOCK) ON c.[nodeId] = n.[id]
JOIN 
    [dbo].[cmsMember] m WITH (NOLOCK) ON m.[nodeId] = c.[nodeId]
JOIN 
    [dbo].[umbracoContentVersion] cv WITH (NOLOCK) ON cv.[nodeId] = m.[nodeId] AND cv.[Current] = 1
LEFT JOIN 
    [dbo].[cmsPropertyType] pt1 WITH (NOLOCK) ON pt1.[contentTypeId] = c.[ContentTypeId] AND pt1.[Alias] = 'umbracoMemberLastLogin'
LEFT JOIN 
    [dbo].[umbracoPropertyData] p1 WITH (NOLOCK) ON p1.[versionId] = cv.[id] AND p1.[propertyTypeId] = pt1.[id]
LEFT JOIN 
    [dbo].[cmsPropertyType] pt5 WITH (NOLOCK) ON pt5.[contentTypeId] = c.[ContentTypeId] AND pt5.[Alias] = 'schoolName'
LEFT JOIN 
    [dbo].[umbracoPropertyData] p5 WITH (NOLOCK) ON p5.[versionId] = cv.[id] AND p5.[propertyTypeId] = pt5.[id]
LEFT JOIN 
    [dbo].[cmsPropertyType] pt6 WITH (NOLOCK) ON pt6.[contentTypeId] = c.[ContentTypeId] AND pt6.[Alias] = 'postcode'
LEFT JOIN 
    [dbo].[umbracoPropertyData] p6 WITH (NOLOCK) ON p6.[versionId] = cv.[id] AND p6.[propertyTypeId] = pt6.[id]
WHERE  
    n.[level] = 1
AND 
    n.[trashed] = 0
"""

# Execute the query and store the result in a pandas DataFrame
try:
    df = pd.read_sql(query, conn)
except db.Error as e:
    st.error(f"Error running query: {e}")
    st.stop()

# Submit button
if st.button("Submit"):
    if postcode_input or school_name_input:
        # Start with the full DataFrame
        filtered_df = df

        # Apply filters if provided
        if postcode_input:
            filtered_df = filtered_df[filtered_df['postcode'].str.contains(postcode_input, na=False, case=False)]

        if school_name_input:
            filtered_df = filtered_df[filtered_df['schoolName'].str.contains(school_name_input, na=False, case=False)]

        # Check if filtered DataFrame is empty
        if filtered_df.empty:
            st.warning("No records found for the entered search criteria.")
        else:
            st.success(f"Found {len(filtered_df)} records matching the search criteria.")
            st.dataframe(filtered_df)  # Display the filtered DataFrame
    else:
        st.warning("Please enter at least one search Criteria.")

# Close the database connection when done
conn.close()

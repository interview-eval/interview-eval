import ast
import os
import re

import pandas as pd


# Function to remove illegal characters
def clean_illegal_chars(s):
    if isinstance(s, str):
        return re.sub(r"[\x00-\x1F\x7F]", "", s)
    return s


# Load CSV file into a pandas DataFrame
input_path = "outputs/0919"  # Replace with your CSV file path
# find all the csv files in the directory
files = [f for f in os.listdir(input_path) if f.endswith(".csv")]
# use for loop to load all the files in the files

for file in files:
    df = pd.read_csv(os.path.join(input_path, file))
    # df['sessions'] = df['session_history'].apply(lambda x: "\n".join(ast.literal_eval(clean_illegal_chars(x))))
    # save dataframe to an excel file
    excel_file = file.replace(".csv", ".xlsx").replace("/0919", "/0919_excel")
    df.to_excel(os.path.join("outputs/0919_excel", excel_file))

# Copyright (C) 2020 Cancer Care Associates

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from pymedphys._imports import pandas as pd
from pymedphys._imports import streamlit as st

from pymedphys._streamlit.utilities import dbf, misc

DB_RELATIONSHIPS = {
    "frame": {"PIMG_DBID": ["patimg", "DBID"]},
    "patimg": {"PORT_DBID": ["port", "DBID"]},
    "port": {"TRT_DBID": ["trtmnt", "DBID"]},
    "trtmnt": {"PAT_DBID": ["patient", "DBID"]},
}


@st.cache()
def get_files(directory, extension):
    return [
        str(item.relative_to(directory)) for item in directory.glob(f"**/*{extension}")
    ]


def main():
    st.title("iView Database Explorer")

    _, database_directory = misc.get_site_and_directory("Database Site", "iviewdb")

    database_paths = {
        path.stem.lower(): path
        for path in database_directory.glob("*.dbf")
        if not path.stem.endswith("_N")
    }

    table_records = {
        key: dbf.get_dbf_table(path) for key, path in database_paths.items()
    }

    table_to_view = st.radio("Table to view", list(table_records.keys()))

    dbf_record = table_records[table_to_view]

    st.write("## Field Names")

    field_names = dbf_record.field_names

    selected_fields = st.multiselect(
        "Field names to view", field_names, default=field_names
    )

    if selected_fields:
        full_pandas_table = pd.DataFrame(iter(dbf_record))
        st.write(full_pandas_table[selected_fields])

    st.write("## File lists")

    if st.button("Show *.jpg files"):
        st.write(get_files(database_directory, ".jpg"))

    if st.button("Show *.xml files"):
        st.write(get_files(database_directory, ".xml"))

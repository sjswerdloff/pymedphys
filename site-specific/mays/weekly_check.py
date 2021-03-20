import os

import streamlit as st

import pandas as pd

from datetime import date, timedelta
from compare import weekly_check_color_results
from weekly_check_helpers import (
    show_incomplete_weekly_checks,
    compare_delivered_to_planned,
    compare_all_incompletes,
    compare_single_incomplete,
    get_delivered_fields,
    plot_couch_positions,
)

currdir = os.getcwd()

st.title("Weekly Check")


incomplete_qcls = show_incomplete_weekly_checks()
incomplete_qcls = incomplete_qcls.drop_duplicates(subset=["patient_id"])
incomplete_qcls = incomplete_qcls.set_index("patient_id")

planned, delivered, overall_results = compare_all_incompletes(incomplete_qcls)
overall_results = overall_results.set_index("patient_id")

weekly_check_results = pd.concat([incomplete_qcls, overall_results], axis=1, sort=True)
weekly_check_results = weekly_check_results.sort_values(["first_name"])
weekly_check_results = weekly_check_results.reset_index()
weekly_check_results_stylized = weekly_check_results.style.apply(
    weekly_check_color_results, axis=1
)
st.write(weekly_check_results_stylized)

default = pd.DataFrame(["< Select a patient >"])
patient_list = (
    weekly_check_results["patient_id"]
    + ", "
    + weekly_check_results["first_name"]
    + " "
    + weekly_check_results["last_name"]
)
patient_list = pd.concat([default, patient_list]).reset_index(drop=True)
patient_select = st.selectbox("Select a patient: ", patient_list[0])

if patient_select is not "< Select a patient >":
    mrn = patient_select.split(",")[0]
    # planned, delivered, patient_results = compare_single_incomplete(mrn)
    todays_date = date.today()
    week_ago = timedelta(days=7)
    delivered = get_delivered_fields(mrn)
    delivered_this_week = delivered[delivered["date"] > todays_date - week_ago]

    # plot the couch coordinates for each delivered beam
    # st.write(planned)
    # st.write(delivered_this_week)
    st.header(
        delivered_this_week.iloc[0]["first_name"]
        + " "
        + delivered_this_week.iloc[0]["last_name"]
    )
    st.write(
        delivered_this_week[
            [
                "date",
                "fraction",
                "total_dose_delivered",
                "site",
                "field_name",
                "was_overridden",
                "partial_treatment",
                "new_field",
            ]
        ].style.background_gradient(cmap="Greys")
    )
    # st.write(delivered)
    # st.write(patient_results)

    plot_couch_positions(delivered)

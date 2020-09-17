import logging
import os
import subprocess
import tempfile
from os.path import basename, exists
from os.path import join as pjoin
from shutil import copyfile

import pytest

import pydicom

from pymedphys._dicom.anonymise import (
    _anonymise_dataset,
    _anonymise_file,
    anonymise_dataset,
    anonymise_file,
    is_anonymised_directory,
    is_anonymised_file,
)
from pymedphys._dicom.constants.core import DICOM_SOP_CLASS_NAMES_MODE_PREFIXES
from pymedphys._dicom.utilities import remove_file
from pymedphys.experimental import pseudonymisation as pseudonymisation_api
from pymedphys.tests.dicom.test_anonymise import (
    dicom_dataset_from_dict,
    get_test_filepaths,
)


@pytest.mark.pydicom
def test_pseudonymise_file():
    identifying_keywords_for_pseudo = (
        pseudonymisation_api.get_default_pseudonymisation_keywords()
    )
    assert "PatientID" in identifying_keywords_for_pseudo
    assert "SOPInstanceUID" in identifying_keywords_for_pseudo
    logging.info("Using pseudonymisation keywords")
    replacement_strategy = pseudonymisation_api.get_copy_of_strategy()
    logging.info("Using pseudonymisation strategy")
    logging.info(
        "replacement strategy self-identifies as %s",
        replacement_strategy["strategy_name"],
    )
    for test_file_path in get_test_filepaths():
        _test_pseudonymise_file_at_path(
            test_file_path,
            test_identifying_keywords=identifying_keywords_for_pseudo,
            test_replacement_strategy=replacement_strategy,
        )


@pytest.mark.pydicom
def test_identifier_with_unknown_vr():
    # The fundamental feature being tested is behaviour in
    # response to a programmer error.
    # The programmer error is specification of an identifier that has a VR
    # that has not been addressed in the strategy.
    # However, because the strategy is only applied when the identifier is found
    # in the dataset, the error will only surface in that circumstance
    replacement_strategy = pseudonymisation_api.get_copy_of_strategy()
    logging.info("Using pseudonymisation strategy")
    identifying_keywords_with_vr_unknown_to_strategy = ["CodingSchemeURL", "PatientID"]
    logging.info("Using keyword with VR = UR")

    # test the new "is_valid_strategy_for_keywords", which should indicate
    # that for the keywords supplied, the strategy will fail should it find
    # the keyword in the data (there is a VR it doesn't support)
    assert not pseudonymisation_api.is_valid_strategy_for_keywords(
        identifying_keywords=identifying_keywords_with_vr_unknown_to_strategy
    )
    ds_input = pydicom.Dataset()
    ds_input.PatientID = "ABC123"
    # not expected to cause problems if the identifier with unknown VR is not in the data
    assert (
        _anonymise_dataset(
            ds_input,
            replacement_strategy=replacement_strategy,
            identifying_keywords=identifying_keywords_with_vr_unknown_to_strategy,
        )
        is not None
    )

    # should raise the error if the identifier with unknown VR is in the data
    with pytest.raises(KeyError):
        ds_input.CodingSchemeURL = "https://scheming.coders.co.nz"
        ds_pseudo = _anonymise_dataset(
            ds_input,
            replacement_strategy=replacement_strategy,
            identifying_keywords=identifying_keywords_with_vr_unknown_to_strategy,
        )
        logging.warning(ds_pseudo)
        logging.warning(ds_input)


@pytest.mark.pydicom
def test_identifier_is_sequence_vr():
    replacement_strategy = pseudonymisation_api.get_copy_of_strategy()
    logging.info("Using pseudonymisation strategy")
    identifying_keywords_no_SQ = ["PatientID", "RequestedProcedureID"]
    identifying_keywords_with_SQ_vr = [
        "PatientID",
        "RequestedProcedureID",
        "RequestAttributesSequence",
    ]

    identifying_requested_procedure_id = "Tumour Identification"
    non_identifying_scheduled_procedure_step_id = "Tumour ID with Dual Energy"
    ds_input = dicom_dataset_from_dict(
        {
            "PatientID": "ABC123",
            "RequestAttributesSequence": [
                {
                    "RequestedProcedureID": identifying_requested_procedure_id,
                    "ScheduledProcedureStepID": non_identifying_scheduled_procedure_step_id,
                }
            ],
        }
    )
    # reality check.  earlier attempt at the input
    # was flawed based on a misunderstanding of dicom_dataset_from_dict
    assert ds_input.RequestAttributesSequence[0].RequestedProcedureID is not None

    ds_anon = _anonymise_dataset(
        ds_input,
        replacement_strategy=replacement_strategy,
        identifying_keywords=identifying_keywords_with_SQ_vr,
    )
    # demonstrate that the entire sequence is emptied out
    # even though that might make the data fail compliance (if the sequence has type 1
    # or type 2)
    assert "RequestedProcedureID" not in ds_anon.RequestAttributesSequence[0]

    ds_anon = _anonymise_dataset(
        ds_input,
        replacement_strategy=replacement_strategy,
        identifying_keywords=identifying_keywords_no_SQ,
    )
    # The sequence is not emptied out
    assert ds_anon.RequestAttributesSequence is not None
    assert ds_anon.RequestAttributesSequence[0] is not None

    assert ds_anon.RequestAttributesSequence[0].RequestedProcedureID is not None
    assert ds_anon.RequestAttributesSequence[0].ScheduledProcedureStepID is not None
    # but an element in the sequence that is an identifier has been pseudonymised
    assert (
        ds_anon.RequestAttributesSequence[0].RequestedProcedureID
        != identifying_requested_procedure_id
    )
    # and an element in the sequence that is not an identifier has been left as is
    assert (
        ds_anon.RequestAttributesSequence[0].ScheduledProcedureStepID
        == non_identifying_scheduled_procedure_step_id
    )


def _test_pseudonymise_file_at_path(
    test_file_path, test_identifying_keywords=None, test_replacement_strategy=None
):
    assert not is_anonymised_file(test_file_path)
    if test_identifying_keywords is None:
        identifying_keywords_for_pseudo = (
            pseudonymisation_api.get_default_pseudonymisation_keywords()
        )
        logging.info("Using pseudonymisation keywords")
    else:
        identifying_keywords_for_pseudo = test_identifying_keywords
    if test_replacement_strategy is None:
        replacement_strategy = pseudonymisation_api.get_copy_of_strategy()
        logging.info("Using pseudonymisation strategy")
    else:
        replacement_strategy = test_replacement_strategy

    ds_input = pydicom.dcmread(test_file_path, force=True)
    ds_pseudo = anonymise_dataset(ds_input, replacement_strategy=replacement_strategy)
    assert ds_pseudo[0x0008, 0x0018].value != ds_input[0x0008, 0x0018].value

    with tempfile.TemporaryDirectory() as output_directory:
        pseudonymised_file_path = _anonymise_file(
            dicom_filepath=test_file_path,
            output_filepath=output_directory,
            delete_original_file=False,
            anonymise_filename=True,
            replace_values=True,
            # keywords_to_leave_unchanged=None,
            delete_private_tags=True,
            delete_unknown_tags=True,
            replacement_strategy=replacement_strategy,
            identifying_keywords=identifying_keywords_for_pseudo,
        )
        # debug print + Assert to force the print
        # print("Pseudonymised file at: ", pseudonymised_file_path)
        # assert False
        assert exists(pseudonymised_file_path)
        ds_input = pydicom.dcmread(test_file_path, force=True)
        ds_pseudo = pydicom.dcmread(pseudonymised_file_path, force=True)
        # simplistic stand-in to make sure *something* is happening
        assert ds_input["PatientID"].value != ds_pseudo["PatientID"].value
        # make sure that we are not accidentally using the hardcode replacement approach
        assert ds_pseudo["PatientID"].value not in ["", "Anonymous"]
        new_sop_instance_uid = ds_pseudo.SOPInstanceUID
        # Filename is anonymised?
        assert new_sop_instance_uid in basename(pseudonymised_file_path)

    # test with public API
    with tempfile.TemporaryDirectory() as output_directory:
        pseudonymised_file_path = anonymise_file(
            dicom_filepath=test_file_path,
            output_filepath=output_directory,
            delete_original_file=False,
            anonymise_filename=True,
            replacement_strategy=replacement_strategy,
        )
        # debug print + Assert to force the print
        # print("Pseudonymised file at: ", pseudonymised_file_path)
        # assert False
        assert exists(pseudonymised_file_path)
        ds_input = pydicom.dcmread(test_file_path, force=True)
        ds_pseudo = pydicom.dcmread(pseudonymised_file_path, force=True)
        # simplistic stand-in to make sure *something* is happening
        assert ds_input["PatientID"].value != ds_pseudo["PatientID"].value
        # make sure that we are not accidentally using the hardcode replacement approach
        assert ds_pseudo["PatientID"].value not in ["", "Anonymous"]
        new_sop_instance_uid = ds_pseudo.SOPInstanceUID
        old_sop_instance_uid = ds_input.SOPInstanceUID
        # UID got anonymised, in some fashion
        assert new_sop_instance_uid != old_sop_instance_uid
        # Filename is anonymised?
        assert new_sop_instance_uid in basename(pseudonymised_file_path)


@pytest.mark.slow
@pytest.mark.pydicom
@pytest.mark.skipif(
    "SUBPACKAGE" in os.environ, reason="Need to extract CLI out of subpackages"
)
def test_pseudonymise_cli(tmp_path):
    for test_file_path in get_test_filepaths():
        _test_pseudonymise_cli_for_file(tmp_path, test_file_path)


def _test_pseudonymise_cli_for_file(tmp_path, test_file_path):

    temp_filepath = pjoin(tmp_path, "test.dcm")
    try:
        logging.info("CLI test on %s", test_file_path)

        copyfile(test_file_path, temp_filepath)

        # Basic file pseudonymisation
        # Initially, just make sure it exits with zero and doesn't fail to generate output
        assert not is_anonymised_file(temp_filepath)

        # need the SOP Instance UID and SOP Class name to figure out the destination file name
        # but will also be using the dataset to do some comparisons.
        ds_input: pydicom.FileDataset = pydicom.dcmread(temp_filepath, force=True)

        pseudo_sop_instance_uid = pseudonymisation_api.get_copy_of_strategy()["UI"](
            ds_input.SOPInstanceUID
        )

        sop_class_uid: pydicom.dataelem.DataElement = ds_input.SOPClassUID

        mode_prefix = DICOM_SOP_CLASS_NAMES_MODE_PREFIXES[
            sop_class_uid.name  # pylint: disable = no-member
        ]
        temp_anon_filepath = pjoin(
            tmp_path,
            "{}.{}_Anonymised.dcm".format(mode_prefix, pseudo_sop_instance_uid),
        )
        assert not exists(temp_anon_filepath)

        anon_file_command = "pymedphys --verbose experimental dicom anonymise --pseudo".split() + [
            temp_filepath
        ]
        logging.warning("Command line: %s", anon_file_command)
        try:
            subprocess.check_call(anon_file_command)
            assert exists(temp_anon_filepath)
            # assert is_anonymised_file(temp_anon_filepath)
            assert exists(temp_filepath)

            ds_pseudo = pydicom.dcmread(temp_anon_filepath, force=True)
            assert ds_input["PatientID"].value != ds_pseudo["PatientID"].value
        finally:
            remove_file(temp_anon_filepath)

        # Basic dir anonymisation
        assert not is_anonymised_directory(tmp_path)
        assert not exists(temp_anon_filepath)

        anon_dir_command = "pymedphys --verbose experimental dicom anonymise --pseudo".split() + [
            str(tmp_path)
        ]
        try:
            subprocess.check_call(anon_dir_command)
            # assert is_anonymised_file(temp_anon_filepath)
            assert exists(temp_filepath)
        finally:
            remove_file(temp_anon_filepath)
    finally:
        remove_file(temp_filepath)

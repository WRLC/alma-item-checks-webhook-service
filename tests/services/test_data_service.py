"""Test suite for DataService"""
import datetime

import pytest

from alma_item_checks_webhook_service.services.data_service import (
    DataService,
    DataSerializationError,
)


class TestDataService:
    """Tests for the DataService class."""

    def setup_method(self):
        """Set up the test class."""
        self.service = DataService()

    # Tests for create_safe_filename
    @pytest.mark.parametrize(
        "input_string, expected_output",
        [
            ("simple_filename", "simple_filename"),
            ("file with spaces", "file_with_spaces"),
            ("path/to/file", "path_to_file"),
            ("file:with?special*chars<>|", "file_with_special_chars"),
            ("  leading and trailing spaces  ", "leading_and_trailing_spaces"),
            ("a" * 250, "a" * 200),
            ("", "default_filename"),
            ("__just_unsafe__", "just_unsafe"),
            ("a//b:c*d", "a_b_c_d"),
        ],
    )
    def test_create_safe_filename(self, input_string, expected_output):
        assert self.service.create_safe_filename(input_string) == expected_output

    def test_create_safe_filename_custom_replacement(self):
        assert (
            self.service.create_safe_filename("file with spaces", replacement="-")
            == "file-with-spaces"
        )

    # Tests for serialize_data
    def test_serialize_data_dict(self):
        data = {"key": "value", "number": 123}
        expected_json = '{"key": "value", "number": 123}'
        assert self.service.serialize_data(data) == expected_json

    def test_serialize_data_list(self):
        data = ["apple", "banana", {"cherry": "red"}]
        expected_json = '["apple", "banana", {"cherry": "red"}]'
        assert self.service.serialize_data(data) == expected_json

    def test_serialize_data_non_ascii(self):
        data = {"key": "valeur_en_français"}
        expected_json = '{"key": "valeur_en_français"}'
        assert self.service.serialize_data(data) == expected_json

    def test_serialize_data_failure(self):
        # datetime objects are not serializable by default
        data = {"time": datetime.datetime.now()}
        with pytest.raises(DataSerializationError):
            self.service.serialize_data(data)

    # Tests for deserialize_data
    def test_deserialize_data_string(self):
        json_string = '{"key": "value"}'
        expected_dict = {"key": "value"}
        assert self.service.deserialize_data(json_string) == expected_dict

    def test_deserialize_data_bytes(self):
        json_bytes = b'[{"key": "value"}]'
        expected_list = [{"key": "value"}]
        assert self.service.deserialize_data(json_bytes) == expected_list

    def test_deserialize_data_invalid_json(self):
        with pytest.raises(DataSerializationError):
            self.service.deserialize_data("{")  # Malformed JSON

    def test_deserialize_data_invalid_bytes(self):
        with pytest.raises(DataSerializationError):
            self.service.deserialize_data(b"\x80abc")  # Invalid UTF-8

    def test_deserialize_data_invalid_type(self):
        with pytest.raises(DataSerializationError):
            # noinspection PyTypeChecker
            self.service.deserialize_data(12345)  # Not a string or bytes

    # Tests for format_datetime_for_display
    def test_format_datetime_naive(self):
        dt = datetime.datetime(2023, 1, 1, 12, 30)
        expected_str = "2023-01-01 12:30:00 UTC"
        assert self.service.format_datetime_for_display(dt) == expected_str

    def test_format_datetime_aware(self):
        tz = datetime.timezone(datetime.timedelta(hours=-5))
        dt = datetime.datetime(2023, 1, 1, 7, 30, tzinfo=tz)
        expected_str = "2023-01-01 07:30:00 UTC-05:00"
        assert (
            self.service.format_datetime_for_display(
                dt, fmt="%Y-%m-%d %H:%M:%S %Z"
            )
            == expected_str
        )

    def test_format_datetime_none(self):
        assert self.service.format_datetime_for_display(None) == ""

    def test_format_datetime_custom_format(self):
        dt = datetime.datetime(2023, 1, 1)
        assert (
            self.service.format_datetime_for_display(dt, fmt="%d-%b-%Y")
            == "01-Jan-2023"
        )

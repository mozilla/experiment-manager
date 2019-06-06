import mock
from requests.exceptions import RequestException, HTTPError
from django.test import TestCase
from experimenter.experiments.normandy import (
    APINormandyError,
    NonsuccessfulNormandyCall,
    NormandyDecodeError,
    make_normandy_call,
    get_recipe,
)
from experimenter.experiments.tests.mixins import MockNormandyMixin


class TestMakeNormandyCall(MockNormandyMixin, TestCase):

    def test_sucessful_call(self):
        mock_response_data = {"detail": "Not found."}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        self.mock_normandy_requests_get.return_value = mock_response

        response_data = make_normandy_call("/url/")

        self.assertEqual(response_data, mock_response_data)

    def test_make_normandy_call_with_request_exception(self):
        self.mock_normandy_requests_get.side_effect = RequestException()

        with self.assertRaises(APINormandyError) as e:
            make_normandy_call("/url/")
            self.assertEqual(
                e.message, "Normandy API returned Nonsuccessful Response Code"
            )

    def test_make_normandy_call_with_HTTP_error(self):
        self.mock_normandy_requests_get.side_effect = HTTPError()
        with self.assertRaises(NonsuccessfulNormandyCall) as e:
            make_normandy_call("/url/")
            self.assertEqual(e.message, "Error calling Normandy API")

    def test_make_normandy_call_with_value_error(self):
        self.mock_normandy_requests_get.side_effect = ValueError()
        with self.assertRaises(NormandyDecodeError) as e:
            make_normandy_call("/url/")
            self.assertEqual(e.message, "Error parsing JSON Normandy Response")

    def test_get_recipe(self):
        response_data = get_recipe(1234)
        self.assertTrue(response_data["enabled"])

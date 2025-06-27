from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from datetime import datetime, timezone

from insights.sources.contacts.clients import FlowsContactsRestClient


class TestFlowsContactsRestClient(TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.client = FlowsContactsRestClient()
        self.project_uuid = "test-project-uuid"
        self.flow_uuid = "test-flow-uuid"
        self.op_field = "test_field"
        self.label = "test_label"
        self.user = "test_user"
        self.ended_at_gte = datetime(2023, 1, 1, tzinfo=timezone.utc)
        self.ended_at_lte = datetime(2023, 12, 31, tzinfo=timezone.utc)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_success(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test successful retrieval of flows contacts."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "John Doe"
        mock_update_contact.return_value = mock_contact_name

        # Mock the Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 25},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "contact-1",
                            "created_on": "2023-06-15T10:30:00Z",
                            "contact_name": "John Doe",
                            "contact_urn": "tel:+1234567890",
                        }
                    },
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "contact-2",
                            "created_on": "2023-06-14T15:45:00Z",
                            "contact_name": "Jane Smith",
                            "contact_urn": "tel:+0987654321",
                        }
                    },
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
            page_number=1,
            page_size=10,
        )

        # Assertions
        self.assertIn("pagination", result)
        self.assertIn("contacts", result)
        self.assertEqual(result["pagination"]["current_page"], 1)
        self.assertEqual(
            result["pagination"]["total_pages"], 3
        )  # 25 items / 10 per page = 3 pages
        self.assertEqual(result["pagination"]["total_items"], 25)
        self.assertEqual(len(result["contacts"]), 2)

        # Check first contact
        first_contact = result["contacts"][0]
        self.assertEqual(first_contact["contact"]["name"], "John Doe")
        self.assertEqual(first_contact["urn"], "tel:+1234567890")
        self.assertEqual(first_contact["start"], "2023-06-15T10:30:00Z")
        self.assertIn("link", first_contact)
        self.assertEqual(first_contact["link"]["type"], "external")

        # Verify the request was made correctly
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        self.assertEqual(call_args[0][0], f"{settings.FLOWS_ES_DATABASE}/_search")

        # Check params
        params = call_args[1]["params"]
        self.assertEqual(
            params["_source"],
            "project_uuid,contact_uuid,created_on,contact_name,contact_urn",
        )
        self.assertEqual(params["from"], 0)
        self.assertEqual(params["size"], 10)

        # Check query structure
        query = call_args[1]["json"]
        self.assertIn("query", query)
        self.assertIn("bool", query["query"])
        self.assertIn("must", query["query"]["bool"])

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_pagination(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test pagination functionality."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock the Elasticsearch response for page 2
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 50},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "contact-11",
                            "created_on": "2023-06-10T10:30:00Z",
                            "contact_name": "Test Contact",
                            "contact_urn": "tel:+1111111111",
                        }
                    }
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method for page 2
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
            page_number=2,
            page_size=10,
        )

        # Assertions
        self.assertEqual(result["pagination"]["current_page"], 2)
        self.assertEqual(
            result["pagination"]["total_pages"], 5
        )  # 50 items / 10 per page = 5 pages
        self.assertEqual(result["pagination"]["total_items"], 50)

        # Verify the request was made with correct pagination
        call_args = mock_requests_get.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["from"], 10)  # (2-1) * 10 = 10
        self.assertEqual(params["size"], 10)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_empty_response(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test handling of empty response from Elasticsearch."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock empty Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
        )

        # Assertions
        self.assertEqual(result["pagination"]["total_items"], 0)
        self.assertEqual(result["pagination"]["total_pages"], 0)
        self.assertEqual(len(result["contacts"]), 0)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_contact_name_fallback(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test fallback to contact_name when UpdateContactName returns None."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName to return None
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = None
        mock_update_contact.return_value = mock_contact_name

        # Mock the Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "contact-1",
                            "created_on": "2023-06-15T10:30:00Z",
                            "contact_name": "Fallback Name",
                            "contact_urn": "tel:+1234567890",
                        }
                    }
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
        )

        # Assertions
        self.assertEqual(result["contacts"][0]["contact"]["name"], "Fallback Name")

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_default_parameters(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test method with default parameters."""
        # Mock the date formatting
        mock_format_date.side_effect = [None, None]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock empty Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        mock_requests_get.return_value = mock_response

        # Call the method with minimal parameters
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
        )

        # Assertions
        self.assertEqual(result["pagination"]["current_page"], 1)
        self.assertEqual(result["pagination"]["page_size"], 10)

        # Verify the request was made with default pagination
        call_args = mock_requests_get.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["from"], 0)
        self.assertEqual(params["size"], 10)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_string_parameters(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test method with string parameters for page_number and page_size."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock empty Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        mock_requests_get.return_value = mock_response

        # Call the method with string parameters
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
            page_number="3",
            page_size="5",
        )

        # Assertions
        self.assertEqual(result["pagination"]["current_page"], 3)
        self.assertEqual(result["pagination"]["page_size"], 5)

        # Verify the request was made with correct pagination
        call_args = mock_requests_get.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["from"], 10)  # (3-1) * 5 = 10
        self.assertEqual(params["size"], 5)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_none_parameters(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test method with None parameters for page_number and page_size."""
        # Mock the date formatting
        mock_format_date.side_effect = [None, None]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock empty Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        mock_requests_get.return_value = mock_response

        # Call the method with None parameters
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
            page_number=None,
            page_size=None,
        )

        # Assertions
        self.assertEqual(result["pagination"]["current_page"], 1)
        self.assertEqual(result["pagination"]["page_size"], 10)

        # Verify the request was made with default pagination
        call_args = mock_requests_get.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["from"], 0)
        self.assertEqual(params["size"], 10)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_missing_source_fields(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test handling of missing source fields in Elasticsearch response."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock Elasticsearch response with missing fields
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            # Missing most fields
                        }
                    }
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
        )

        # Assertions
        self.assertEqual(len(result["contacts"]), 1)
        contact = result["contacts"][0]
        self.assertEqual(
            contact["contact"]["name"], "Test Contact"
        )  # From UpdateContactName
        self.assertEqual(contact["urn"], "")  # Default empty string
        self.assertEqual(contact["start"], "")  # Default empty string
        self.assertIn("link", contact)
        self.assertEqual(contact["link"]["type"], "external")

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_single_contact(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test handling of single contact response."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Single Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock Elasticsearch response with single contact
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "single-contact-1",
                            "created_on": "2023-06-15T10:30:00Z",
                            "contact_name": "Single Contact",
                            "contact_urn": "tel:+1234567890",
                        }
                    }
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
        )

        # Assertions
        self.assertEqual(result["pagination"]["total_items"], 1)
        self.assertEqual(result["pagination"]["total_pages"], 1)
        self.assertEqual(len(result["contacts"]), 1)

        contact = result["contacts"][0]
        self.assertEqual(contact["contact"]["name"], "Single Contact")
        self.assertEqual(contact["urn"], "tel:+1234567890")
        self.assertEqual(contact["start"], "2023-06-15T10:30:00Z")

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_large_page_size(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test with large page size to ensure proper pagination calculation."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 100},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "contact-1",
                            "created_on": "2023-06-15T10:30:00Z",
                            "contact_name": "Test Contact",
                            "contact_urn": "tel:+1234567890",
                        }
                    }
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method with large page size
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
            page_size=50,
        )

        # Assertions
        self.assertEqual(result["pagination"]["page_size"], 50)
        self.assertEqual(
            result["pagination"]["total_pages"], 2
        )  # 100 items / 50 per page = 2 pages
        self.assertEqual(result["pagination"]["total_items"], 100)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_with_pk_parameter(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test method with pk parameter (should be ignored but covered)."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock empty Elasticsearch response
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        mock_requests_get.return_value = mock_response

        # Call the method with pk parameter
        result = self.client.get_flows_contacts(
            pk="some-pk-value",
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
        )

        # Assertions - pk should be ignored
        self.assertEqual(result["pagination"]["current_page"], 1)
        self.assertEqual(result["pagination"]["page_size"], 10)

    @patch("insights.sources.contacts.clients.requests.get")
    @patch("insights.sources.contacts.clients.get_token_flows_authentication")
    @patch("insights.sources.contacts.clients.UpdateContactName")
    @patch("insights.sources.contacts.clients.format_to_iso_utc")
    def test_get_flows_contacts_exact_page_calculation(
        self, mock_format_date, mock_update_contact, mock_get_token, mock_requests_get
    ):
        """Test exact page calculation when total items is exactly divisible by page size."""
        # Mock the date formatting
        mock_format_date.side_effect = ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

        # Mock the flows token
        mock_get_token.return_value = "test_token"

        # Mock the UpdateContactName
        mock_contact_name = MagicMock()
        mock_contact_name.get_contact_name.return_value = "Test Contact"
        mock_update_contact.return_value = mock_contact_name

        # Mock Elasticsearch response with exactly 20 items
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "total": {"value": 20},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": self.project_uuid,
                            "contact_uuid": "contact-1",
                            "created_on": "2023-06-15T10:30:00Z",
                            "contact_name": "Test Contact",
                            "contact_urn": "tel:+1234567890",
                        }
                    }
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        # Call the method with page size 10
        result = self.client.get_flows_contacts(
            project_uuid=self.project_uuid,
            flow_uuid=self.flow_uuid,
            op_field=self.op_field,
            label=self.label,
            user=self.user,
            ended_at_gte=self.ended_at_gte,
            ended_at_lte=self.ended_at_lte,
            page_size=10,
        )

        # Assertions
        self.assertEqual(result["pagination"]["total_items"], 20)
        self.assertEqual(
            result["pagination"]["total_pages"], 2
        )  # 20 items / 10 per page = 2 pages exactly

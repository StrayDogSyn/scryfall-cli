import unittest
from unittest.mock import Mock, patch

import requests

import api_client


class ApiClientTests(unittest.TestCase):
    @patch("api_client.time.sleep")
    @patch("api_client.requests.get")
    def test_fetch_card_sends_expected_request(self, mock_get, mock_sleep):
        response = Mock(status_code=200)
        response.json.return_value = {"name": "Lightning Bolt"}
        mock_get.return_value = response

        result = api_client.fetch_card_by_name("lightning bolt")

        self.assertEqual(result["name"], "Lightning Bolt")
        mock_sleep.assert_called_once_with(0.1)
        mock_get.assert_called_once_with(
            f"{api_client.BASE_URL}/cards/named",
            params={"fuzzy": "lightning bolt"},
            headers=api_client._headers(),
            timeout=api_client.TIMEOUT,
        )
        response.raise_for_status.assert_called_once_with()

    @patch("api_client.time.sleep")
    @patch("api_client.requests.get")
    def test_fetch_card_distinguishes_ambiguous_404(self, mock_get, _mock_sleep):
        response = Mock(status_code=404)
        response.json.return_value = {"details": "Too many cards matched that query."}
        mock_get.return_value = response

        with self.assertRaises(api_client.CardNotFoundError) as raised:
            api_client.fetch_card_by_name("jace")

        self.assertTrue(raised.exception.ambiguous)

    @patch("api_client.time.sleep")
    @patch("api_client.requests.get")
    def test_fetch_card_translates_network_errors(self, mock_get, _mock_sleep):
        cases = [
            (
                requests.exceptions.Timeout("raw"),
                requests.exceptions.Timeout,
                "did not respond within 10s",
            ),
            (
                requests.exceptions.ConnectionError("raw"),
                requests.exceptions.ConnectionError,
                "Could not reach Scryfall",
            ),
            (
                requests.exceptions.RequestException("raw"),
                requests.exceptions.RequestException,
                "Unexpected network error",
            ),
        ]

        for source, expected_type, expected_message in cases:
            with self.subTest(source=type(source).__name__):
                mock_get.side_effect = source
                with self.assertRaises(expected_type) as raised:
                    api_client.fetch_card_by_name("bolt")
                self.assertIn(expected_message, str(raised.exception))

    @patch("api_client.time.sleep")
    @patch("api_client.requests.get")
    def test_search_returns_first_page_data(self, mock_get, _mock_sleep):
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"name": "Goblin Guide"}], "has_more": True}
        mock_get.return_value = response

        result = api_client.search_cards("t:goblin")

        self.assertEqual(result, [{"name": "Goblin Guide"}])
        mock_get.assert_called_once_with(
            f"{api_client.BASE_URL}/cards/search",
            params={"q": "t:goblin"},
            headers=api_client._headers(),
            timeout=api_client.TIMEOUT,
        )

    @patch("api_client.time.sleep")
    @patch("api_client.requests.get")
    def test_search_404_raises_not_found(self, mock_get, _mock_sleep):
        mock_get.return_value = Mock(status_code=404)

        with self.assertRaises(api_client.CardNotFoundError):
            api_client.search_cards("no:matches")


if __name__ == "__main__":
    unittest.main()

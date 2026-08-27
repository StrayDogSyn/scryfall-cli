import argparse
import contextlib
import io
import unittest
from unittest.mock import patch

import requests

import main
from api_client import CardNotFoundError


class MainCommandTests(unittest.TestCase):
    def capture(self, function, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = function(args)
        return result, output.getvalue()

    @patch("main.display.print_card_detail")
    @patch("main.extract_card_summary")
    @patch("main.fetch_card_by_name")
    def test_lookup_success(self, fetch, extract, print_detail):
        fetch.return_value = {"name": "Lightning Bolt"}
        extract.return_value = {"name": "Lightning Bolt", "price_usd": 0.79}

        result = main.cmd_lookup(argparse.Namespace(name="lightning bolt"))

        self.assertEqual(result, 0)
        fetch.assert_called_once_with("lightning bolt")
        extract.assert_called_once_with(fetch.return_value)
        print_detail.assert_called_once_with(extract.return_value)

    @patch("main.fetch_card_by_name")
    def test_lookup_rejects_blank_input_without_network_call(self, fetch):
        result, output = self.capture(main.cmd_lookup, argparse.Namespace(name="   "))

        self.assertEqual(result, 1)
        self.assertIn("Card name cannot be empty", output)
        fetch.assert_not_called()

    @patch("main.fetch_card_by_name")
    def test_lookup_reports_not_found_and_ambiguous_errors(self, fetch):
        for ambiguous, expected in [
            (False, "No card found"),
            (True, "matched several cards"),
        ]:
            with self.subTest(ambiguous=ambiguous):
                fetch.side_effect = CardNotFoundError("missing", ambiguous=ambiguous)
                result, output = self.capture(
                    main.cmd_lookup,
                    argparse.Namespace(name="jace"),
                )
                self.assertEqual(result, 1)
                self.assertIn(expected, output)

    @patch("main.fetch_card_by_name")
    def test_lookup_reports_request_errors(self, fetch):
        fetch.side_effect = requests.exceptions.Timeout("timed out")

        result, output = self.capture(
            main.cmd_lookup,
            argparse.Namespace(name="lightning bolt"),
        )

        self.assertEqual(result, 1)
        self.assertIn("timed out", output)

    @patch("main.display.print_comparison")
    @patch("main.compare_cards")
    @patch("main.fetch_card_by_name")
    def test_compare_success(self, fetch, compare, print_comparison):
        fetch.side_effect = [{"name": "A"}, {"name": "B"}]
        compare.return_value = {"a": {"name": "A"}, "b": {"name": "B"}}

        result = main.cmd_compare(argparse.Namespace(name_a="A", name_b="B"))

        self.assertEqual(result, 0)
        self.assertEqual(fetch.call_count, 2)
        print_comparison.assert_called_once_with(compare.return_value)

    @patch("main.display.print_card_list")
    @patch("main.search_cards")
    def test_search_success(self, search, print_list):
        search.return_value = [{"name": "Goblin Guide"}]

        result = main.cmd_search(argparse.Namespace(query="t:goblin"))

        self.assertEqual(result, 0)
        search.assert_called_once_with("t:goblin")
        print_list.assert_called_once_with(search.return_value)

    def test_parser_dispatches_supported_commands(self):
        parser = main.build_parser()

        lookup = parser.parse_args(["lookup", "sol ring"])
        compare = parser.parse_args(["compare", "black lotus", "mox pearl"])
        search = parser.parse_args(["search", "t:goblin"])

        self.assertEqual((lookup.command, lookup.name), ("lookup", "sol ring"))
        self.assertEqual(compare.command, "compare")
        self.assertEqual((compare.name_a, compare.name_b), ("black lotus", "mox pearl"))
        self.assertEqual((search.command, search.query), ("search", "t:goblin"))


if __name__ == "__main__":
    unittest.main()

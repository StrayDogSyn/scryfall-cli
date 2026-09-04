import contextlib
import io
import unittest

import display


class DisplayTests(unittest.TestCase):
    def capture(self, function, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            function(*args)
        return output.getvalue()

    def test_print_card_detail_formats_optional_values(self):
        summary = {
            "name": "Grizzly Bears",
            "mana_cost": "{1}{G}",
            "type_line": "Creature — Bear",
            "rarity": "Common",
            "set_name": "Tenth Edition",
            "released_at": "2007-07-13",
            "price_usd": 0.15,
            "power": "2",
            "toughness": "2",
            "oracle_text": "A simple creature.",
            "artist": "D. J. Cleland-Hura",
        }

        output = self.capture(display.print_card_detail, summary)

        self.assertIn("Grizzly Bears", output)
        self.assertIn("$0.15", output)
        self.assertIn("2/2", output)
        self.assertIn("A simple creature.", output)

    def test_print_card_detail_uses_fallbacks_and_omits_pt(self):
        output = self.capture(
            display.print_card_detail,
            {"name": "Sol Ring", "mana_cost": "", "price_usd": None},
        )

        self.assertIn("Mana Cost      n/a", output)
        self.assertIn("Price (USD)    n/a", output)
        self.assertNotIn("P/T", output)

    def test_print_comparison_formats_both_columns(self):
        comparison = {
            "a": {"name": "Bear", "price_usd": 1.0, "power": "2", "toughness": "2"},
            "b": {"name": "Ring", "price_usd": None},
        }

        output = self.capture(display.print_comparison, comparison)

        self.assertIn("Name: Bear", output)
        self.assertIn("Name: Ring", output)
        self.assertIn("Price (USD): $1.00", output)
        self.assertIn("P/T: 2/2", output)
        self.assertIn("P/T: n/a", output)

    def test_print_comparison_handles_asymmetric_power_and_toughness(self):
        comparison = {
            "a": {"name": "Partial", "power": "2"},
            "b": {"name": "Also Partial", "toughness": "3"},
        }

        output = self.capture(display.print_comparison, comparison)

        self.assertEqual(output.count("P/T: n/a"), 2)

    def test_print_card_list_handles_results_and_empty_list(self):
        cards = [{
            "name": "Lightning Bolt",
            "type_line": "Instant",
            "rarity": "uncommon",
            "prices": {"usd": "0.79"},
        }]

        output = self.capture(display.print_card_list, cards)
        empty_output = self.capture(display.print_card_list, [])

        self.assertIn("Lightning Bolt", output)
        self.assertIn("$0.79", output)
        self.assertIn("1 result(s) returned.", output)
        self.assertIn("No cards to display.", empty_output)

    def test_print_card_list_handles_invalid_usd_price(self):
        cards = [{"name": "Mystery Card", "prices": {"usd": "unknown"}}]

        output = self.capture(display.print_card_list, cards)

        self.assertIn("Mystery Card", output)
        self.assertIn("n/a", output)

    def test_print_error_uses_consistent_prefix(self):
        output = self.capture(display.print_error, "Something went wrong.")

        self.assertIn("Error: Something went wrong.", output)


if __name__ == "__main__":
    unittest.main()

import unittest

from card_data import compare_cards, extract_card_summary, get_legality, get_price


class CardDataTests(unittest.TestCase):
    def test_extract_card_summary_normalizes_fields(self):
        card = {
            "name": "Grizzly Bears",
            "mana_cost": "{1}{G}",
            "cmc": 2,
            "type_line": "Creature — Bear",
            "rarity": "common",
            "set_name": "Tenth Edition",
            "oracle_text": "",
            "artist": "D. J. Cleland-Hura",
            "released_at": "2007-07-13",
            "prices": {"usd": "0.15"},
            "power": "2",
            "toughness": "2",
        }

        summary = extract_card_summary(card)

        self.assertEqual(summary["rarity"], "Common")
        self.assertEqual(summary["price_usd"], 0.15)
        self.assertEqual(summary["power"], "2")
        self.assertEqual(summary["toughness"], "2")

    def test_extract_card_summary_omits_missing_power_and_toughness(self):
        summary = extract_card_summary({"name": "Sol Ring"})

        self.assertNotIn("power", summary)
        self.assertNotIn("toughness", summary)
        self.assertIsNone(summary["price_usd"])

    def test_extract_card_summary_omits_asymmetric_power_and_toughness(self):
        for card in ({"power": "2"}, {"toughness": "2"}):
            with self.subTest(card=card):
                summary = extract_card_summary(card)
                self.assertNotIn("power", summary)
                self.assertNotIn("toughness", summary)

    def test_get_price_handles_missing_null_and_invalid_values(self):
        cases = [
            ({}, None),
            ({"prices": None}, None),
            ({"prices": {"usd": None}}, None),
            ({"prices": {"usd": "not-a-price"}}, None),
            ({"prices": {"usd": "1.25"}}, 1.25),
        ]

        for card, expected in cases:
            with self.subTest(card=card):
                self.assertEqual(get_price(card), expected)

    def test_get_legality_returns_status_or_unknown(self):
        card = {"legalities": {"modern": "legal", "legacy": "banned"}}

        self.assertEqual(get_legality(card, "modern"), "legal")
        self.assertEqual(get_legality(card, "legacy"), "banned")
        self.assertEqual(get_legality(card, "standard"), "unknown")
        self.assertEqual(get_legality({}, "standard"), "unknown")

    def test_compare_cards_builds_two_summaries(self):
        result = compare_cards(
            {"name": "Black Lotus", "prices": {"usd": None}},
            {"name": "Mox Pearl", "prices": {"usd": "100.00"}},
        )

        self.assertEqual(result["a"]["name"], "Black Lotus")
        self.assertEqual(result["b"]["name"], "Mox Pearl")
        self.assertEqual(result["b"]["price_usd"], 100.0)


if __name__ == "__main__":
    unittest.main()

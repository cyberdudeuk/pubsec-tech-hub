"""Every check must pass on the real repository and fail on a known-bad sample."""
import copy
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import checks  # noqa: E402
import harvest  # noqa: E402

FIX = Path(__file__).parent / "fixtures"


def bad_state():
    s = copy.deepcopy(checks.load_state())
    d = s["data"]
    s["html"] = s["html"].replace("</body>", '<p>Write to someone@example.gov.uk. Operated by the Central Digital and Data Office. Crown Copyright 2025</p>'
                                  '<script src="https://example.com/x.js"></script><script>eval("1")</script><a data-form="9-missing.yml"></a></body>')
    s["html"] = s["html"].replace("prefers-reduced-motion", "prefers-x").replace('<script type="application/ld+json">', '<script type="application/ld+json">{')
    s["html"] = s["html"].replace("minutes a week", "minutes") + "x" * checks.MAX_BYTES
    d["sources"]["SX"] = {"t": "x", "url": "http://insecure.example"}
    d["listings"][0]["figures"].append({"t": "x", "s": "S999"})
    d["listings"][0]["rating"] = 4.8
    d["listings"][1]["maturity"] = "Certified"
    d["listings"][2]["code"] = ["ftp://x"]
    d["listings"][3]["id"] = d["listings"][4]["id"]
    d["requirements"][0][2] = ["N99"]
    d["requirements"][1][4] = ["no_such_check"]
    d["defects"][0][5] = []
    d["directories"] = [x for x in d["directories"] if "NHS login" not in x["n"]]
    d["ecosystem"]["Communities"].append({"n": "A think tank", "u": "https://x.example", "label": "think tank"})
    s["reconciliation"]["rows"][0][5] = "Maybe"
    s["forms"].pop("3-claim.yml")
    s["workflows"]["x.yml"] = "jobs:\n  a:\n    steps:\n      - uses: actions/checkout@v4\n"
    return s


class Checks(unittest.TestCase):
    def test_all_pass_on_real_repository(self):
        failures = {k: v for k, v in checks.run(checks.load_state()).items() if v}
        self.assertEqual(failures, {})

    def test_every_check_fails_on_bad_sample(self):
        results = checks.run(bad_state())
        for name, problems in results.items():
            with self.subTest(check=name):
                self.assertTrue(problems, f"{name} did not fail on the bad sample")

    def test_every_check_is_known_to_requirements(self):
        self.assertTrue({"no_emails", "search_finds", "visual_qa"} <= checks.known_checks())


class Build(unittest.TestCase):
    def test_qr_svg_is_normalised(self):
        """D8: the QR code must serialise the same with or without lxml, or CI reports a stale site."""
        import build  # noqa: E402
        svg = build.qr_svg("https://example.org/")
        self.assertNotIn(" />", svg)
        self.assertTrue(svg.startswith("<svg"))


class Harvest(unittest.TestCase):
    def setUp(self):
        self.doc = yaml.safe_load((FIX / "publiccode.yml").read_text(encoding="utf-8"))

    def test_harvest_parses(self):
        x = harvest.map_publiccode(self.doc, "https://github.com/example-council/bins")
        self.assertEqual((x["name"], x["maturity"], x["licence"], x["kind"], x["pc"]), ("Example Council Bins", "stable", "MIT", "Product", True))
        self.assertEqual(x["live"], "https://bins.example.org")

    def test_harvest_strips_contacts(self):
        x = harvest.map_publiccode(self.doc, "https://github.com/example-council/bins")
        self.assertNotIn("@", str(x))
        doc = copy.deepcopy(self.doc)
        doc["description"]["en"]["shortDescription"] = "Mail bins@example.org"
        self.assertNotIn("bins@example.org", harvest.map_publiccode(doc, "https://github.com/a/b")["summary"])

    def test_harvest_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            harvest.map_publiccode({"no": "name"}, "https://github.com/a/b")
        with self.assertRaises(ValueError):
            harvest.fetch("https://evil.example/a/b", "main")

    def test_unknown_status_is_not_declared(self):
        doc = dict(self.doc, developmentStatus="certified")
        self.assertEqual(harvest.map_publiccode(doc, "https://github.com/a/b")["maturity"], "Not declared")


if __name__ == "__main__":
    unittest.main()

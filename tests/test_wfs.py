import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wfs import build_lotes_wfs_uri


class LotesWfsUriTests(unittest.TestCase):
    def test_builds_uri_with_only_required_business_filters(self):
        uri = build_lotes_wfs_uri(42, 52)

        self.assertIn("typename='agrae:lotes_campania'", uri)
        self.assertIn("srsname='EPSG:4326'", uri)
        self.assertIn("VIEWPARAMS=idcampania%3A42%3Bidexplotacion%3A52", uri)
        self.assertNotIn("CQL_FILTER", uri)
        self.assertIn("pagingEnabled='false'", uri)
        self.assertIn("restrictToRequestBBOX='0'", uri)
        self.assertNotIn("user=", uri)
        self.assertNotIn("password=", uri)

    def test_rejects_non_integer_filter_values(self):
        for campaign, holding in ((None, 52), ("42 OR 1=1", 52), (42, 0)):
            with self.subTest(campaign=campaign, holding=holding):
                with self.assertRaises(ValueError):
                    build_lotes_wfs_uri(campaign, holding)


if __name__ == "__main__":
    unittest.main()

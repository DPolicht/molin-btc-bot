import io
import json
import unittest
from unittest.mock import patch
from legacy_mean_reversion import fetch

def response(rows):
    return io.BytesIO(json.dumps(rows).encode())

class FeedTests(unittest.TestCase):
    @patch('legacy_mean_reversion.time.sleep')
    @patch('legacy_mean_reversion.urlopen')
    def test_missing_latest_bar_is_refetched_without_synthetic_prices(self,open_url,_):
        open_url.side_effect=[response([[0,99,101,100,100,1]]),
                              response([[0,99,101,100,100,1],[60,100,102,101,101,2]])]
        bars=fetch(0,120)
        self.assertEqual([c.time for c in bars],[0,60])
        self.assertEqual(bars[-1].close,101)
        self.assertEqual(open_url.call_count,2)

    @patch('legacy_mean_reversion.time.sleep')
    @patch('legacy_mean_reversion.urlopen')
    def test_persistent_gap_reports_timestamp_and_fails(self,open_url,_):
        open_url.side_effect=lambda *a,**kw:response([[0,99,101,100,100,1]])
        with self.assertRaisesRegex(RuntimeError,'1970-01-01T00:01:00Z'):
            fetch(0,120)
        self.assertEqual(open_url.call_count,4)

    @patch('legacy_mean_reversion.time.sleep')
    @patch('legacy_mean_reversion.urlopen')
    def test_complete_response_needs_no_backfill(self,open_url,_):
        open_url.return_value=response([[60,100,102,101,101,2],[0,99,101,100,100,1],
                                        [120,101,103,102,102,3]])
        self.assertEqual([c.time for c in fetch(0,120)],[0,60])
        self.assertEqual(open_url.call_count,1)

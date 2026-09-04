import tempfile
import unittest
from pathlib import Path

from country_runner.csvio import read_csv, write_csv
from country_runner.ids import (
    canonicalize_url,
    content_id,
    duplicate_hints,
    evidence_id,
    merge_raw_records,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = PROJECT_ROOT / "country_runner" / "tests" / "fixtures" / "evidence" / "multilingual.csv"


class IdAndDedupTests(unittest.TestCase):
    def test_platform_id_precedes_url_and_is_stable(self) -> None:
        first = content_id(
            source_name="YouTube",
            platform_content_id="abc123",
            item_url="https://youtube.com/watch?v=abc123&utm_source=test",
        )
        moved = content_id(
            source_name="YouTube",
            platform_content_id="abc123",
            item_url="https://youtu.be/abc123?si=tracking",
        )
        self.assertEqual(first, moved)
        self.assertTrue(first.startswith("CNT-"))

    def test_url_fingerprint_ignores_tracking_and_known_youtube_short_links(self) -> None:
        canonical = canonicalize_url(
            "https://www.youtube.com/watch?v=abc123&utm_source=x&feature=shared"
        )
        short = canonicalize_url("https://youtu.be/abc123?si=xyz")
        self.assertEqual(canonical, "https://youtube.com/watch?v=abc123")
        self.assertEqual(short, canonical)
        self.assertEqual(
            content_id("web", "", "https://example.com/post?a=1&utm_campaign=x"),
            content_id("web", "", "https://EXAMPLE.com/post?utm_source=y&a=1#comments"),
        )

    def test_multiple_query_hits_merge_without_losing_provenance(self) -> None:
        rows = [
            {
                "source_name": "YouTube",
                "platform_content_id": "abc123",
                "item_url": "https://youtu.be/abc123",
                "query_hit_ids": "Q-A-1",
                "original_text": "I used it to prepare a CV.",
                "original_text_translation_cn": "",
                "published_at": "2026-08-01",
                "geo_evidence": "Creator states they work in Abu Dhabi.",
            },
            {
                "source_name": "YouTube",
                "platform_content_id": "abc123",
                "item_url": "https://youtube.com/watch?v=abc123&utm_source=x",
                "query_hit_ids": "Q-C-2|Q-A-1",
                "original_text": "",
                "original_text_translation_cn": "我用它来准备简历。",
                "published_at": "",
                "geo_evidence": "",
            },
        ]
        merged = merge_raw_records(rows)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["query_hit_ids"], "Q-A-1|Q-C-2")
        self.assertEqual(merged[0]["original_text"], "I used it to prepare a CV.")
        self.assertEqual(merged[0]["original_text_translation_cn"], "我用它来准备简历。")
        self.assertEqual(merged[0]["published_at"], "2026-08-01")
        self.assertTrue(merged[0]["geo_evidence"])

    def test_evidence_id_is_global_and_does_not_change_when_rows_are_appended(self) -> None:
        first = evidence_id("CNT-abc", "prepare CV from job post")
        duplicate_in_other_stream = evidence_id("CNT-abc", "  Prepare   CV from job post ")
        different_unit = evidence_id("CNT-abc", "sell a paid CV template")
        self.assertEqual(first, duplicate_in_other_stream)
        self.assertNotEqual(first, different_unit)
        before = [first, different_unit]
        after = before + [evidence_id("CNT-new", "draft email")]
        self.assertEqual(after[:2], before)

    def test_duplicate_hints_flag_canonical_and_language_mirror_urls_without_deleting(self) -> None:
        rows = [
            {"content_id": "CNT-1", "item_url": "https://example.com/en/posts/42?utm_source=x"},
            {"content_id": "CNT-2", "item_url": "https://example.com/ar/posts/42"},
            {"content_id": "CNT-3", "item_url": "https://example.com/post/9?ref=home"},
            {"content_id": "CNT-4", "item_url": "https://example.com/post/9"},
        ]
        hints = duplicate_hints(rows)
        self.assertEqual(len(rows), 4)
        self.assertIn({"CNT-1", "CNT-2"}, [set(hint["content_ids"]) for hint in hints])
        exact = next(hint for hint in hints if set(hint["content_ids"]) == {"CNT-3", "CNT-4"})
        self.assertEqual(exact["reason"], "canonical_url")

    def test_csv_round_trip_preserves_multilingual_quotes_and_newlines(self) -> None:
        rows = read_csv(FIXTURE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "roundtrip.csv"
            write_csv(output, list(rows[0]), rows)
            reread = read_csv(output)
        self.assertEqual(reread, rows)
        self.assertIn("\n", rows[0]["original_text"])
        self.assertIn(" مفيد", rows[0]["original_text"])
        self.assertEqual(rows[1]["language"], "ja")
        self.assertEqual(rows[2]["language"], "hi")


if __name__ == "__main__":
    unittest.main()

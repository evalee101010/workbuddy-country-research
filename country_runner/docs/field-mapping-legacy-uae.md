# UAE legacy evidence migration mapping

The maintenance migration reads the three 2026 UAE pilot CSV files without modifying them. It writes their original row IDs to `legacy_record_id`, keeps the shortest captured original quotation and Chinese translation verbatim, and stores the full legacy row in `raw_fields_json` for auditability.

## Mapping decisions

| Legacy input | New destination | Important mapping |
|---|---|---|
| `04-raw-feedback.csv` | `raw-discovery-log.csv` | `feedback_id` → `legacy_record_id`; original quote/translation, date and geo evidence retained |
| `05-coded-feedback.csv` | `A-competitor-feedback.csv` | joins to raw feedback by `feedback_id`; stable `content_id` and `evidence_id` added |
| `16-kol-uae-multichannel-samples.csv` | raw log and `C-kol-koc-content.csv` | `sample_id` → `legacy_record_id`; `emirate_name` → `admin1_name`; `audience_geo_confidence` preserved |

Legacy review URLs sometimes point to paginated listing pages rather than item permalinks. To avoid collapsing distinct reviews, migration uses the stable legacy record ID as an identity surrogate while keeping `platform_content_id` empty. Canonical-URL matches are emitted only as duplicate hints; no row is deleted automatically.

Blank new fields remain blank. In particular, migration does not infer clicks, audience roles, offer prices, exact dates, technical level, or country confidence that was absent from the source.

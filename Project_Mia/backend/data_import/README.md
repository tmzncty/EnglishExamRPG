# Curated exam import bundles

This directory stores human-reviewable, reproducible inputs for adding exam papers to
`Project_Mia/backend/data/static_content.db`.

The SQLite database remains the application source of truth. Bundles here are imported
by `scripts/import_exam_bundle.py`; the normal export script then regenerates
`Project_Mia/backend/data_export`.

## 2026 English I

`2026-eng1.json` contains 52 questions / 100 points and is deliberately curated from
multiple public transcriptions rather than copied blindly from one OCR result.

Verification notes:

- Reading A was cross-checked against an independent sentence-by-sentence transcription.
- One circulating PDF duplicates the Q21 C/D option text. The bundle restores Q21 C as
  “They were tamed at an earlier time than horses,” which is also supported directly by
  the passage and independent transcriptions.
- 2026 Reading Part B has eight paragraph choices (A–H). The bundle stores A–H explicitly
  so the frontend does not fall back to its legacy A–G default.
- Writing B embeds a deterministic SVG reconstruction of the chart using the printed
  percentages, so the task remains usable without keeping a binary exam PDF in the repo.

Source URLs and cross-check provenance are recorded inside the JSON bundle itself.

To validate and import locally:

```bash
python Project_Mia/backend/scripts/import_exam_bundle.py \
  Project_Mia/backend/data_import/2026-eng1.json
python Project_Mia/backend/scripts/export_static_content_text.py
```

The importer is idempotent. If the SQLite rows already match the bundle, it performs no
database write.

# VisionSpace Agent Instructions

Follow these instructions before editing this repository. This file is for coding agents; `README.md` is the human-facing Turkish setup and architecture document.

## Required Reading

Before changing a subsystem, read its local system guide:

- Root project overview and setup: `README.md`
- Data crawler and preprocessor: `data/SYSTEM.md`
- Backend AI service: `ai-service/SYSTEM.md`
- Flutter mobile app: `flutter-app/SYSTEM.MD`
- Original product/use-case notes, when relevant: `TEMP/TEMP.md`

Do not infer architecture, data contracts, design rules, or operational flow from isolated files if the relevant `SYSTEM.md` file covers the topic. If you change architecture, API contracts, auth assumptions, data flow, UI flow, localization, or setup steps, update the affected `SYSTEM.md` and, when human setup changes, update `README.md` too.

## Repository Map

- `data/`: Scrapy-based product data pipeline. `crawler/` collects raw furniture products and downloads images into `data/output/`; `preprocessor/` normalizes products, enriches taxonomy/semantic text with Vertex AI or deterministic fallback, and writes `enriched_products.jsonl`. It does not build production embeddings; `ai-service` does that during indexing.
- `ai-service/`: FastAPI backend for room-design jobs, uploads, product search, persistence, and background AI workflow execution. It uses PostgreSQL, Redis/RQ, Qdrant, LangGraph, and Vertex AI. Product import and Qdrant indexing scripts live in `ai-service/scripts/`.
- `flutter-app/`: Flutter mobile client. It handles onboarding, home/design/product screens, room scan brief, camera capture, upload to `ai-service`, background job polling, result display, profile settings, localization, and local notifications.
- Firebase/Firestore files under `flutter-app/`: Firebase config, Firestore rules/indexes, and seed data for curated design content. Backend-trusted AI operations should go through `ai-service`, not directly from the Flutter client.
- `TEMP/`: Temporary/original requirement notes. Use these when validating intended use cases or preserving earlier product decisions.

## Cross-System Flow

1. `data/crawler` scrapes source stores into raw JSONL and image files.
2. `data/preprocessor` creates enriched product JSONL.
3. `ai-service/scripts/import_enriched.py` imports enriched records into PostgreSQL.
4. `ai-service/scripts/index_products_qdrant.py` generates Vertex text/image embeddings and writes Qdrant vectors.
5. `flutter-app` sends scan uploads and design-job requests to `ai-service`.
6. `ai-service` runs long AI stages in the worker and returns completed designs for the app to display.

## Module Rules

### Data Pipeline

- Keep crawler source parsing in `data/crawler/spiders/` or `data/crawler/extractors/`.
- Keep schema normalization, enrichment prompts, fallback enrichment, and Vertex preprocessor calls in `data/preprocessor/`.
- Preprocessor Vertex auth uses a service account JSON key via `GOOGLE_APPLICATION_CREDENTIALS`; do not add API-key Gemini calls or personal ADC fallback.
- Preserve JSONL as the boundary between crawler, preprocessor, and backend import.
- Do not reintroduce preprocessor vector-building scripts unless the backend indexing design changes and the system docs are updated.

### AI Service Backend

- Keep API routes under `ai-service/app/api/routes/`, business orchestration under `services/`, DB access under `db/`, workflow nodes under `workflow/nodes/`, and vector logic under `vector/`.
- Long AI work must remain in the RQ worker path, not blocking Flutter-facing request handlers.
- Product embeddings and Qdrant writes are owned by `ai-service` indexing.
- Service account credentials belong in `ai-service/secrets/` and must stay uncommitted.
- For backend changes, run focused pytest targets when possible. If Docker services or dependencies are unavailable, report the exact gap.

### Flutter App

- Localize every user-facing string. Labels, buttons, placeholders, SnackBars, error messages, empty states, semantic labels, dialog text, and test expectations must come from localization resources.
- Update both `flutter-app/lib/l10n/app_en.arb` and `flutter-app/lib/l10n/app_tr.arb` whenever adding or editing user-facing text.
- Use generated `AppLocalizations` from widget `BuildContext` after adding localization keys.
- Follow the visual style, color palette, navigation, and domain-model guidance in `flutter-app/SYSTEM.MD`.
- Backend connectivity must go through the app backend configuration/client layer, not hard-coded endpoint strings inside UI widgets.
- When creating or editing a widget, add or update focused widget tests.
- Before finishing UI work, run at minimum `flutter analyze` and `flutter test` when the environment supports it. For platform-specific changes, run the relevant build or targeted check.

## Change Safety

- Check `git status --short` before editing.
- Treat existing modifications as user-owned.
- Do not revert, overwrite, or reformat unrelated files.
- If a file you must edit already has user changes, read it carefully and preserve the user’s work.
- Keep edits scoped to the requested subsystem and update docs in the same change when behavior or setup changes.

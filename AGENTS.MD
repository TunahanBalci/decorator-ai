# decorator-ai Agent Instructions

Follow these instructions before editing this repository.

## Required Reading

- Read `SYSTEM.MD` whenever you need project architecture, product design, visual design, navigation, domain model, service, localization, or testing details.
- Do not guess design rules from isolated files if `SYSTEM.MD` contains the relevant guidance.

## Hard Constraints

- Localize every user-facing string. Any text visible to users, including labels, buttons, placeholders, SnackBars, error messages, empty states, semantic labels, dialog text, and test expectations, must come from localization resources rather than hard-coded UI strings.
- Update both `lib/l10n/app_en.arb` and `lib/l10n/app_tr.arb` whenever adding or editing user-facing text.
- Use generated `AppLocalizations` access from widget `BuildContext` after adding localization keys.
- Follow the visual style and color palette documented in `SYSTEM.MD`.
- When creating or editing a widget, always create or update focused widget tests and verify they pass.
- Run verification before finishing UI work: at minimum `flutter analyze` and `flutter test`. If a platform-specific change is made, run the relevant platform build or targeted check as well.
- If any architectural or design changes are made, update `SYSTEM.MD` in the same change so it remains accurate. This is a hard constraint.

## Change Safety

- Check `git status --short` before editing.
- Treat existing modifications as user-owned.
- Do not revert, overwrite, or reformat unrelated files.
- If a file you must edit already has user changes, read it carefully and preserve the user’s work.

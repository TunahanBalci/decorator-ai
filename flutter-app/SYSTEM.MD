# decorator-ai System Guide

This file contains the project architecture, product design, visual design system, and implementation conventions for agents working in this repository. Agents must read this file before making UI, architecture, service, navigation, localization, or test changes.

## Project Overview

decorator-ai is a Flutter app named `decorator_ai` in `pubspec.yaml`. It is an AI-assisted interior design and shopping experience:

- Users enter through a welcome screen.
- The main app shell exposes Home, Scan, Saved, and Profile tabs.
- Users can browse AI design suggestions, inspect generated rooms, tap product hotspots, and open matched store links.
- The scan flow opens the device camera, captures a room image, and currently returns mock AI analysis data.
- Firebase Core is initialized at startup with generated `firebase_options.dart`; Firestore is the planned database.
- AI service calls and certain backend operations are expected to go through a separate server API, not directly through Firebase. That server is not set up yet.
- Cloud Functions may be added later for Firebase-adjacent automation, but no Cloud Functions are currently implemented.

The app currently targets Flutter Android builds. The active product surface is a mobile-first Material 3 experience constrained around a narrow phone layout in several screens.

## Repository Layout

- `lib/main.dart`: Flutter entrypoint, Firebase initialization, `MaterialApp`, global theme, supported locales, and home route.
- `lib/core/theme/`: Shared design tokens and theme.
- `lib/core/widgets/`: Reusable UI primitives.
- `lib/navigation/app_shell.dart`: Bottom-tab shell and placeholder tab pages.
- `lib/features/welcome/`: First-run welcome and app entry screen.
- `lib/features/onboarding/`: Optional first-run personalization questions before entering the main shell, including a Redux-backed onboarding state store.
- `lib/features/home/`: Home feed with mock AI design project cards.
- `lib/features/scan/`: Scan landing page and camera capture/analyze flow.
- `lib/features/design/`: Design detail page with room image hotspots and product list.
- `lib/features/product/`: Product detail page and store offer links.
- `lib/models/`: Plain immutable domain models.
- `lib/services/`: API abstraction, current Firestore read/write implementation, and mock fallback implementation.
- `lib/l10n/`: ARB localization files.
- `test/`: Flutter widget tests.
- `firestore.rules`: Firestore security rules.
- `firestore.indexes.json`: Firestore composite index definitions.
- `firestore_seed/`: Seed data for curated design projects and product hotspots.
- Platform folders currently present: `android/`. iOS, Linux, web, Windows, and macOS platform folders were removed.

## App Bootstrapping

`main()` in `lib/main.dart`:

- Calls `WidgetsFlutterBinding.ensureInitialized()`.
- Initializes Firebase with `DefaultFirebaseOptions.currentPlatform`.
- Runs `DecoratorAiApp`.

`DecoratorAiApp` builds the root `MaterialApp`:

- `debugShowCheckedModeBanner: false`
- `theme: AppTheme.light`
- `home: _StartupPage`, which reads `SharedPreferences` and opens either `WelcomePage` for first entry or `AppShell` with the persisted selected tab after the user has completed or skipped onboarding.
- Supported locales are English (`en`) and Turkish (`tr`).
- Generated `AppLocalizations` and Flutter localization delegates are configured.

Localization note: `pubspec.yaml` has `flutter: generate: true`, `l10n.yaml` points at `lib/l10n`, and generated localization classes are written to `lib/l10n/app_localizations*.dart`. `MaterialApp` uses `AppLocalizations.delegate`, global Flutter localization delegates, and `AppLocalizations.supportedLocales`.

## Navigation Flow

Navigation is currently simple and imperative:

- `WelcomePage` uses `Navigator.pushReplacement` to enter `OnboardingFlowPage`. Its scan CTA starts onboarding with Scan as the target tab, while its examples CTA starts onboarding with Home as the target tab.
- `OnboardingFlowPage` shows one optional question per page, persists any provided answers in `SharedPreferences`, then marks the user as entered and opens `AppShell` on the target tab.
- `AppShell` keeps tab state in `_index`, persists the selected tab in `SharedPreferences`, and renders pages with `IndexedStack`.
- On app startup after first entry, `_StartupPage` restores the last persisted shell tab.
- The Home scan promotion card selects the Scan tab through an `AppShell` callback.
- The Scan tab opens `CameraScanPage` with `Navigator.push`.
- `CameraScanPage` pushes replacement to `DesignDetailPage` after mock analysis succeeds.
- `HomePage` project cards push `DesignDetailPage`.
- `DesignDetailPage` hotspots and product tiles push `ProductDetailPage`.
- Detail pages use local back buttons that call `Navigator.pop`.

Do not introduce a routing package unless the app’s navigation complexity actually requires it.

## Domain Model

`DesignProject`:

- `id`
- `title`
- `spaceType`
- `style`
- `imageUrl`
- `products: List<ProductSpot>`

`ProductSpot`:

- `id`
- `name`
- `brand`
- `price`
- `matchScore`
- `left` and `top` as normalized hotspot coordinates from `0.0` to `1.0`
- `imageUrl`
- `buyUrl`

`StoreOffer`:

- `storeName`
- `price`
- `url`
- `buttonColor`

Keep models small and immutable unless real API integration requires parsing, serialization, or validation helpers.

## Service Layer

`lib/services/decorator_ai_api.dart` defines:

- `DecoratorAiApi`
- `FirestoreDecoratorAiApi`
- `MockDecoratorAiApi`

The intended backend architecture is split:

- Firestore is the database for app data such as published design projects, product hotspots, and queued scan metadata.
- A separate server API is expected to own AI service calls and backend operations that should not run from the client.
- That server API is not set up yet, so the current app must keep using the service abstraction and mock fallback behavior.
- Cloud Functions may be introduced later for event-driven Firebase workflows, but do not assume they exist or route AI calls through them.

`FirestoreDecoratorAiApi` currently reads published design projects from Firestore and falls back to `MockDecoratorAiApi` when Firestore is unavailable or empty. The camera analysis path writes a queued scan document to `scans` and then falls back to mock analysis until the separate backend/AI server exists.

Firestore collections:

- `designProjects/{projectId}`: curated room/design cards shown on Home and Design Detail.
- `designProjects/{projectId}/products/{productId}`: product hotspots and matched shopping items for a design.
- `scans/{scanId}`: queued scan submissions from the camera flow.

`designProjects` documents use `title`, `spaceType`, `style`, `imageUrl`, `isPublished`, and `sortOrder`.

`products` subcollection documents use `name`, `brand`, `price`, `matchScore`, `left`, `top`, `imageUrl`, `buyUrl`, and `sortOrder`.

`scans` documents use `localScanId`, `status`, and `createdAt`.

Deploy Firestore rules and indexes with:

```sh
firebase deploy --only firestore
```

Seed data lives in `firestore_seed/design_projects.json`; import it with the Firebase CLI or copy the documents manually in the Firebase Console.

The mock service returns static `DesignProject` data and simulates latency with short `Future.delayed` calls.

When replacing the mock AI analysis with the real server API:

- Preserve the abstraction boundary so UI widgets do not own networking details.
- Keep Firestore as the database unless the product architecture changes explicitly.
- Do not put privileged AI provider credentials, server-only prompts, billing logic, or trusted moderation decisions in the Flutter client.
- Model server responses with typed DTOs or domain mapping in the service layer.
- Add typed parsing and error handling in the service layer.
- Keep UI states explicit: loading, success, empty, recoverable error, and permission error where relevant.
- Add tests around service behavior or widget behavior using fakes.

If Cloud Functions are added later:

- Document each function's trigger, input, output, permissions, and deployment command in this guide.
- Keep Cloud Functions separate from the app client contract unless the client calls a callable/HTTP function directly.
- Update Firestore rules and indexes alongside function behavior when data access patterns change.

## Visual Design System

The app uses a warm, editorial interior-design look with Material 3:

- Background: warm off-white `AppColors.background` (`0xFFF6F1EA`)
- Surface cards: white `AppColors.surface`
- Primary text and filled controls: near-black `AppColors.ink`
- Secondary copy: muted warm gray `AppColors.muted`
- Borders: pale warm gray `AppColors.border`
- Supporting accents: `sand`, `clay`, `sage`, and `violet`

Typography:

- `AppTheme.light` sets `fontFamily: 'Arial'`.
- Headline styles are heavy and compact.
- Body text uses moderate size and relaxed line height.
- Existing UI uses strong weights (`w700` to `w900`) for product, button, and card labels.

Shape and spacing:

- The current app favors rounded image panels and cards, often `20` to `34` px radii.
- Primary buttons are 56 px high with 18 px radius.
- Bottom navigation is a floating dark rounded bar, 66 px high, with selected white pill state.
- Mobile content commonly uses horizontal padding around `20` to `24` px and bottom padding to clear the floating nav.
- Screens that should read as phone-first often use `ConstrainedBox(maxWidth: 430)`.

Image treatment:

- Use `RemoteImage` for remote network images so failures display the app’s sand fallback.
- Room/design imagery is usually clipped with large radii and may use dark gradients for legibility.
- Product imagery appears in clipped rectangular panels or small rounded thumbnails.

Controls:

- Prefer `PrimaryButton` for primary and outlined call-to-action buttons.
- Prefer Material icons already used by the app.
- Use `IconButton.filled` for compact circular page actions where consistent with existing screens.

Do not introduce a conflicting palette, dense new typography scale, or unrelated visual style. Extend `AppColors` or shared widgets only when a value is reused or clearly part of the design system.

## Localization Requirements

Localization files:

- `l10n.yaml`
- `lib/l10n/app_en.arb`
- `lib/l10n/app_tr.arb`
- `lib/l10n/app_localizations*.dart` generated by `flutter gen-l10n`

Current UI-authored visible copy is expected to use generated `AppLocalizations` lookups. Future work must preserve and improve coverage rather than add hard-coded visible strings.

Required workflow for visible copy:

1. Add or update a descriptive key in `app_en.arb`.
2. Add or update the matching key in `app_tr.arb`.
3. Include ARB metadata descriptions for non-obvious English keys.
4. Run Flutter localization generation through normal Flutter commands, usually as part of `flutter analyze`, `flutter test`, or `flutter gen-l10n`.
5. Read strings from `AppLocalizations` in widgets.
6. Update tests to pump the app with localization delegates and assert localized text.

Use placeholders for dynamic text such as product counts, match scores, store names, prices, and camera error details. Do not concatenate localized sentences from fragments unless the fragments are standalone labels.

Examples of text that must be localized:

- Button labels
- Navigation labels
- Page titles
- Placeholder titles and subtitles
- SnackBar messages
- Camera permission and error messages
- Product count and match score labels
- Security or checkout notes
- Empty/loading/retry messages

Brand names, store names, URLs, product names from backend data, and prices do not need localization unless they are app-authored labels.

## Feature Details

### Welcome

`WelcomePage` presents:

- Brand mark and `decorator-ai` wordmark.
- Turkish hero copy describing room scanning, AI design, and shopping.
- Remote interior hero image.
- Primary scan CTA and outlined example-design CTA.

When editing this page, preserve the image-led editorial layout and large headline rhythm.

### Onboarding

`OnboardingFlowPage` presents optional first-run personalization questions:

- Are you decorating your home from scratch?
- Where is your space located? This stage asks for when-in-use location permission, centers the map on the user location when permitted, and lets the user tap the map to select their area.
- How old are you?
- Are you living alone or with your family?

Each question appears on its own page with one input surface. Text-input stages must autofocus the first relevant input, validate only when the optional field is filled, and allow empty answers to be skipped. The location stage uses `flutter_map` with OpenStreetMap tiles and `geolocator` for the one-time current-location request; if permission or services are unavailable, users can still tap the map manually. The primary action reads as Skip when the page has no answer and Next when it does. The top-left arrow returns to the previous onboarding stage. On completion, the page enters `AppShell` on the target tab selected by the welcome CTA.

Current onboarding answers are stored locally in `SharedPreferences` until a server API exists for profile/personalization persistence. Keep user-facing onboarding strings localized.

Onboarding state uses the `redux` package:

- `OnboardingFlowPage` owns a local `Store<OnboardingState>` rather than app-wide global state.
- `onboarding_store.dart` defines the immutable state, actions, and reducer for stage transitions, optional answers, and validation errors.
- Use Redux for new onboarding state changes so UI controls dispatch actions instead of mutating widget fields directly.
- Do not expand Redux to unrelated app state without a specific architecture decision.

### App Shell

`AppShell` uses:

- `IndexedStack` to preserve tab page state.
- Dark floating bottom navigation with selected white pill.
- Four tabs: Home, Scan, Saved placeholder, Profile placeholder.

Any new tab content must leave enough bottom padding for the floating nav.

### Home

`HomePage`:

- Fetches projects once from `MockDecoratorAiApi`.
- Displays a brand/header row, notification action, dark scan promotion panel, and design project cards.
- Project cards use large room images, dark bottom gradient, title, metadata, and circular arrow affordance.

If adding loading, empty, or error states, keep them visually consistent and localized.

### Scan

`ScanPage`:

- Explains the scan flow.
- Shows a dark rounded preview panel with a remote room image and scan frame.
- Opens `CameraScanPage`.

`CameraScanPage`:

- Uses the `camera` plugin.
- Chooses the back camera when available.
- Handles camera absence, access denial, initialization errors, capture errors, and analyzing overlay.
- Captures an image, passes the local path as `scanId`, and navigates to `DesignDetailPage`.

Camera-facing changes need tests where practical and careful manual/platform verification because plugin behavior may differ by platform.

### Design Detail

`DesignDetailPage`:

- Shows design title and metadata.
- Displays a large room image with normalized product hotspots.
- Lists clickable product tiles.

Hotspot coordinates are normalized against the displayed image area. Preserve this contract when changing image layout.

### Product Detail

`ProductDetailPage`:

- Shows product image, name, generated description, rating stub, AI similar-products CTA, store offers, and security note.
- Opens store links with `url_launcher` using `LaunchMode.externalApplication`.
- Shows a SnackBar if a store link cannot be opened.

Store buttons intentionally use brand colors. Keep those colors local to store presentation unless they become shared design tokens.

## Shared Widgets

`PrimaryButton`:

- Full-width, 56 px height.
- Filled style uses `AppColors.ink` with white content.
- Outlined style uses `AppColors.border` and ink content.
- Supports optional leading icon and ellipsized label.

`RemoteImage`:

- Wraps `Image.network`.
- Accepts `url`, `fit`, `width`, and `height`.
- Uses a sand-colored fallback with an image-not-supported icon.

Prefer improving these shared widgets over duplicating equivalent button or network-image behavior in feature files.

## Testing Rules

Current tests live in `test/widget_test.dart` and use `flutter_test`.

For any widget creation or edit:

- Add or update widget tests for the changed behavior.
- Test localized text through the app localization setup.
- Test navigation behavior when a widget’s primary action changes.
- Test loading, empty, error, or permission states when those states are part of the edit.
- Keep tests focused; avoid broad golden-style assertions unless intentionally adding golden coverage.

Required verification commands for normal Flutter changes:

```sh
flutter analyze
flutter test
```

Additional useful commands:

```sh
flutter gen-l10n
flutter test test/widget_test.dart
```

If tests cannot run because of local SDK, plugin, camera, Firebase, or platform configuration problems, document the exact command and failure. Do not claim verification passed unless it actually passed.

## Code Style

- Follow `package:flutter_lints/flutter.yaml` from `analysis_options.yaml`.
- Prefer `const` constructors and widgets where possible.
- Keep widgets small and private to their feature file unless reused across features.
- Use existing folder boundaries: `features`, `core`, `models`, `services`, and `navigation`.
- Keep UI free of direct backend/networking code; use services or injected fakes.
- Avoid unrelated refactors while implementing feature work.
- Do not rename public classes or files casually, even if current names are not idiomatic.
- Keep platform-specific edits scoped to the relevant platform folder.

## Git and Change Safety

The worktree may contain user changes. Before editing:

- Check `git status --short`.
- Treat existing modifications as user-owned.
- Do not revert, overwrite, or reformat unrelated files.
- If a file you must edit already has user changes, read it carefully and preserve the user’s work.

When finishing:

- Summarize changed files and verification results.
- Call out any known localization debt or tests that were not run.

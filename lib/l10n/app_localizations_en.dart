// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Decorator AI';

  @override
  String get appBrand => 'Decorator AI';

  @override
  String get welcomeHeadline =>
      'Scan your real space,\ndesign with AI,\nbuy what you love.';

  @override
  String get welcomeSubtitle =>
      'A smart interior app that analyzes your home, office, or workplace and turns products into tappable shopping points.';

  @override
  String get welcomeInsight =>
      'AI design suggestions and shopping matches are ready.';

  @override
  String get welcomeStartScan => 'Start Scanning the Space';

  @override
  String get welcomeExploreExamples => 'Explore Example Designs';

  @override
  String onboardingStep(int current, int total) {
    return '$current of $total';
  }

  @override
  String get onboardingOptionalSubtitle =>
      'Optional. Share what you want and skip the rest.';

  @override
  String get onboardingSkip => 'Skip';

  @override
  String get onboardingNext => 'Next';

  @override
  String get onboardingYes => 'Yes';

  @override
  String get onboardingNo => 'No';

  @override
  String get onboardingScratchQuestion =>
      'Are you decorating your home from scratch?';

  @override
  String get onboardingLocationQuestion => 'Where is your space located?';

  @override
  String get onboardingLocationSubtitle =>
      'Allow location to start near you, then tap the map to select your area.';

  @override
  String get onboardingUseCurrentLocation => 'Use my location';

  @override
  String get onboardingSelectMapCenter => 'Select map center';

  @override
  String get onboardingLocationMapHint => 'Tap the map to select your area.';

  @override
  String onboardingLocationSelected(Object latitude, Object longitude) {
    return 'Selected: $latitude, $longitude';
  }

  @override
  String get onboardingLocationServiceDisabled =>
      'Location services are off. You can still tap the map.';

  @override
  String get onboardingLocationPermissionDenied =>
      'Location permission was denied. You can still tap the map.';

  @override
  String get onboardingLocationPermissionDeniedForever =>
      'Location permission is blocked. You can still tap the map.';

  @override
  String get onboardingLocationUnavailable =>
      'Current location is unavailable. You can still tap the map.';

  @override
  String get onboardingCountryLabel => 'Country';

  @override
  String get onboardingCountryHint => 'Türkiye, France, United States...';

  @override
  String get onboardingAreaLabel => 'Area';

  @override
  String get onboardingAreaHint => 'Gölbaşı, Le Marais, Manhattan...';

  @override
  String get onboardingLocationInvalid =>
      'Select country, city, and area from the list.';

  @override
  String get onboardingCityQuestion => 'Which city are you located in?';

  @override
  String get onboardingCitySubtitle =>
      'Start typing and choose a city from the list.';

  @override
  String get onboardingCityLabel => 'City';

  @override
  String get onboardingCityHint => 'Istanbul, London, New York...';

  @override
  String get onboardingCityInvalid => 'Choose a city from the list.';

  @override
  String get onboardingAgeQuestion => 'How old are you?';

  @override
  String get onboardingAgeLabel => 'Age';

  @override
  String get onboardingAgeHint => '32';

  @override
  String get onboardingAgeInvalid => 'Enter an age between 16 and 120.';

  @override
  String get onboardingLivingQuestion =>
      'Are you living alone or with your family?';

  @override
  String get onboardingLivingAlone => 'Living alone';

  @override
  String get onboardingLivingFamily => 'With my family';

  @override
  String get navHome => 'Home';

  @override
  String get navScan => 'Scan';

  @override
  String get navSaved => 'Favorites';

  @override
  String get navProfile => 'Profile';

  @override
  String get savedTitle => 'Favorites';

  @override
  String get savedSubtitle => 'Furniture you favorite will be collected here.';

  @override
  String get profileTitle => 'Profile';

  @override
  String get profileSubtitle =>
      'Account, address, and preference settings will connect to the backend.';

  @override
  String get homeSubtitle => 'AI-powered space design';

  @override
  String get homeNewScanBadge => 'New scan';

  @override
  String get homeHeroTitle =>
      'Scan your space,\nwe will create your AI design.';

  @override
  String get homeHeroBody =>
      'Room size, light, style, and product detection will connect to this flow through the backend.';

  @override
  String get homeSuggestionsTitle => 'AI Design Suggestions';

  @override
  String designMatchedProducts(Object spaceType, Object style, int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count products matched',
      one: '1 product matched',
      zero: 'no products matched',
    );
    return '$spaceType • $style • $_temp0';
  }

  @override
  String get designClickableProducts => 'Tappable Products';

  @override
  String productMatchScore(int score) {
    return '$score% match';
  }

  @override
  String get scanTitle => 'Space Scan';

  @override
  String get scanSubtitle =>
      'Open the camera and scan the space to create an AI design.';

  @override
  String get scanInstruction =>
      'When you press the button, the camera opens. After the photo is taken, the AI design flow starts.';

  @override
  String get scanCreateDesign => 'Create AI Design';

  @override
  String get cameraNotFound => 'No camera found.';

  @override
  String get cameraCouldNotStart => 'Camera could not be started.';

  @override
  String get cameraCaptureFailed => 'Scan could not be captured. Try again.';

  @override
  String get cameraAnalyzing => 'AI is analyzing the space...';

  @override
  String get cameraCaptureHint => 'Frame the room, then press the scan button.';

  @override
  String get cameraPermissionDenied =>
      'Camera permission was not granted. Allow camera permission from the browser to scan.';

  @override
  String cameraCouldNotOpen(Object details) {
    return 'Camera could not be opened: $details';
  }

  @override
  String get cameraScanTitle => 'Scan the Space';

  @override
  String get cameraOverlayHint =>
      'Keep the walls, floor, light, and furniture visible so they can be detected.';

  @override
  String get productSimilarWithAi => 'Find Similar Products with AI';

  @override
  String get productPurchaseOptions => 'Purchase Options';

  @override
  String get productDescriptionSofa => 'Modern fabric three-seat sofa';

  @override
  String get productDescriptionGeneric =>
      'A similar product matched by AI according to the item in the design.';

  @override
  String productRatingSummary(Object rating, int reviewCount) {
    return '$rating ($reviewCount)';
  }

  @override
  String get productDetailTitle => 'Product Detail';

  @override
  String get productGoToProduct => 'Go to Product';

  @override
  String productStoreOpenFailed(Object storeName) {
    return '$storeName link could not be opened.';
  }

  @override
  String get productSecurityNote =>
      'You will go to the store\'s official page through a secure redirect.';

  @override
  String get profileSaved => 'Profile saved successfully.';

  @override
  String profileGoogleSignInFailed(String error) {
    return 'Failed to sign in with Google: $error';
  }

  @override
  String get profileDefaultUser => 'User';

  @override
  String get profileNameLabel => 'Name';

  @override
  String get profileSurnameLabel => 'Surname';

  @override
  String get profileNameRequired => 'Name is required';

  @override
  String get profileSurnameRequired => 'Surname is required';

  @override
  String get profileEditCancel => 'Cancel';

  @override
  String get profileEditConfirm => 'Confirm';

  @override
  String get profileSignInGoogle => 'Sign in with Google';

  @override
  String get profileSignOut => 'Sign Out';

  @override
  String get profileBirthdayLabel => 'Birthday';

  @override
  String get profileBirthdayNotSet => 'Birthday not set';

  @override
  String get profileSettingsTitle => 'Settings';

  @override
  String get profileSettingAuthReminders => 'Authentication Reminders';

  @override
  String get profileSettingAiUpdates => 'Design Suggestion Status Updates';

  @override
  String get authReminderTitle => 'Sign in to save your progress!';

  @override
  String get authReminderBody =>
      'Don\'t lose your AI designs. Sign in with Google now.';

  @override
  String get authReminderRecurringTitle => 'Your spaces are waiting';

  @override
  String get authReminderRecurringBody =>
      'Sign in to sync your AI designs across devices.';

  @override
  String get profileSettingLanguage => 'Language';

  @override
  String get languageEnglish => 'English';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get notificationsTitle => 'Notifications';

  @override
  String get noNotificationsMessage => 'There are no notifications';

  @override
  String get noFavoritesMessage =>
      'No favorite furniture yet. Tap a heart on the home screen to add one.';
}

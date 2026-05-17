// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get appTitle => 'Decorator AI';

  @override
  String get appBrand => 'Decorator AI';

  @override
  String get welcomeHeadline =>
      'Gerçek mekanı tara,\nAI ile tasarla,\nbeğendiğini al.';

  @override
  String get welcomeSubtitle =>
      'Ev, ofis veya iş yerini analiz eden; ürünleri tıklanabilir satın alma noktalarına çeviren akıllı iç mekan uygulaması.';

  @override
  String get welcomeInsight =>
      'AI tasarım önerileri ve alışveriş eşleşmeleri hazır.';

  @override
  String get welcomeStartScan => 'Mekanı Taramaya Başla';

  @override
  String get welcomeExploreExamples => 'Örnek Tasarımları Keşfet';

  @override
  String onboardingStep(int current, int total) {
    return '$current / $total';
  }

  @override
  String get onboardingOptionalSubtitle =>
      'İsteğe bağlı. İstediğini paylaş, kalanları atla.';

  @override
  String get onboardingSkip => 'Atla';

  @override
  String get onboardingNext => 'İleri';

  @override
  String get onboardingYes => 'Evet';

  @override
  String get onboardingNo => 'Hayır';

  @override
  String get onboardingScratchQuestion => 'Evini sıfırdan mı dekore ediyorsun?';

  @override
  String get onboardingLocationQuestion => 'Mekanın nerede?';

  @override
  String get onboardingLocationSubtitle =>
      'Yakınından başlamak için konum izni ver, sonra haritada bölgeni seç.';

  @override
  String get onboardingUseCurrentLocation => 'Konumumu kullan';

  @override
  String get onboardingSelectMapCenter => 'Harita merkezini seç';

  @override
  String get onboardingLocationMapHint => 'Bölgeni seçmek için haritaya dokun.';

  @override
  String onboardingLocationSelected(Object latitude, Object longitude) {
    return 'Seçildi: $latitude, $longitude';
  }

  @override
  String get onboardingLocationServiceDisabled =>
      'Konum servisleri kapalı. Yine de haritaya dokunabilirsin.';

  @override
  String get onboardingLocationPermissionDenied =>
      'Konum izni verilmedi. Yine de haritaya dokunabilirsin.';

  @override
  String get onboardingLocationPermissionDeniedForever =>
      'Konum izni engellenmiş. Yine de haritaya dokunabilirsin.';

  @override
  String get onboardingLocationUnavailable =>
      'Mevcut konum alınamadı. Yine de haritaya dokunabilirsin.';

  @override
  String get onboardingCountryLabel => 'Ülke';

  @override
  String get onboardingCountryHint =>
      'Türkiye, Fransa, Amerika Birleşik Devletleri...';

  @override
  String get onboardingAreaLabel => 'Bölge';

  @override
  String get onboardingAreaHint => 'Gölbaşı, Le Marais, Manhattan...';

  @override
  String get onboardingLocationInvalid => 'Listeden ülke, şehir ve bölge seç.';

  @override
  String get onboardingCityQuestion => 'Hangi şehirde yaşıyorsun?';

  @override
  String get onboardingCitySubtitle =>
      'Yazmaya başla ve listeden bir şehir seç.';

  @override
  String get onboardingCityLabel => 'Şehir';

  @override
  String get onboardingCityHint => 'İstanbul, Londra, New York...';

  @override
  String get onboardingCityInvalid => 'Listeden bir şehir seç.';

  @override
  String get onboardingAgeQuestion => 'Kaç yaşındasın?';

  @override
  String get onboardingAgeLabel => 'Yaş';

  @override
  String get onboardingAgeHint => '32';

  @override
  String get onboardingAgeInvalid => '16 ile 120 arasında bir yaş gir.';

  @override
  String get onboardingLivingQuestion => 'Yalnız mı, ailenle mi yaşıyorsun?';

  @override
  String get onboardingLivingAlone => 'Yalnız yaşıyorum';

  @override
  String get onboardingLivingFamily => 'Ailemle yaşıyorum';

  @override
  String get navHome => 'Ana';

  @override
  String get navScan => 'Tara';

  @override
  String get navSaved => 'Favoriler';

  @override
  String get navProfile => 'Profil';

  @override
  String get savedTitle => 'Favoriler';

  @override
  String get savedSubtitle => 'Favorilediğin mobilyalar burada toplanacak.';

  @override
  String get profileTitle => 'Profil';

  @override
  String get profileSubtitle =>
      'Hesap, adres ve tercih ayarları backend ile bağlanacak.';

  @override
  String get homeSubtitle => 'AI destekli mekan tasarımı';

  @override
  String get homeNewScanBadge => 'Yeni tarama';

  @override
  String get homeHeroTitle => 'Mekanını tarat,\nAI tasarımını üretelim.';

  @override
  String get homeHeroBody =>
      'Oda ölçüsü, ışık, stil ve ürün algılama backend ile bu akışa bağlanacak.';

  @override
  String get homeSuggestionsTitle => 'AI Tasarım Önerileri';

  @override
  String designMatchedProducts(Object spaceType, Object style, int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count ürün eşleşti',
      one: '1 ürün eşleşti',
      zero: 'ürün eşleşmedi',
    );
    return '$spaceType • $style • $_temp0';
  }

  @override
  String get designClickableProducts => 'Tıklanabilir Ürünler';

  @override
  String productMatchScore(int score) {
    return '%$score benzerlik';
  }

  @override
  String get scanTitle => 'Mekan Taraması';

  @override
  String get scanSubtitle =>
      'AI tasarım oluşturmak için kamerayı açıp mekanı tarat.';

  @override
  String get scanInstruction =>
      'Butona basınca kamera açılır. Fotoğraf çekildikten sonra AI tasarım akışı başlar.';

  @override
  String get scanCreateDesign => 'AI Tasarım Oluştur';

  @override
  String get cameraNotFound => 'Kamera bulunamadı.';

  @override
  String get cameraCouldNotStart => 'Kamera başlatılamadı.';

  @override
  String get cameraCaptureFailed => 'Tarama alınamadı. Tekrar dene.';

  @override
  String get cameraAnalyzing => 'AI mekanı analiz ediyor...';

  @override
  String get cameraCaptureHint =>
      'Odayı kadraja al, sonra tarama butonuna bas.';

  @override
  String get cameraPermissionDenied =>
      'Kamera izni verilmedi. Tarama yapmak için tarayıcıdan kamera izni ver.';

  @override
  String cameraCouldNotOpen(Object details) {
    return 'Kamera açılamadı: $details';
  }

  @override
  String get cameraScanTitle => 'Mekanı Tara';

  @override
  String get cameraOverlayHint =>
      'Duvar, zemin, ışık ve mobilyaları algılamak için alanı görünür tut.';

  @override
  String get productSimilarWithAi => 'Benzer Ürünleri AI ile Bul';

  @override
  String get productPurchaseOptions => 'Satın Alma Seçenekleri';

  @override
  String get productDescriptionSofa => 'Modern kumaş üçlü koltuk';

  @override
  String get productDescriptionGeneric =>
      'AI tarafından tasarımdaki ürüne göre eşleştirilen benzer ürün.';

  @override
  String productRatingSummary(Object rating, int reviewCount) {
    return '$rating ($reviewCount)';
  }

  @override
  String get productDetailTitle => 'Ürün Detayı';

  @override
  String get productGoToProduct => 'Ürüne Git';

  @override
  String productStoreOpenFailed(Object storeName) {
    return '$storeName linki açılamadı.';
  }

  @override
  String get productSecurityNote =>
      'Güvenli yönlendirme ile mağazanın resmi sayfasına gidersiniz.';

  @override
  String get profileSaved => 'Profil başarıyla kaydedildi.';

  @override
  String profileGoogleSignInFailed(String error) {
    return 'Google ile giriş yapılamadı: $error';
  }

  @override
  String get profileDefaultUser => 'Kullanıcı';

  @override
  String get profileNameLabel => 'Ad';

  @override
  String get profileSurnameLabel => 'Soyad';

  @override
  String get profileNameRequired => 'Ad zorunludur';

  @override
  String get profileSurnameRequired => 'Soyad zorunludur';

  @override
  String get profileEditCancel => 'İptal';

  @override
  String get profileEditConfirm => 'Onayla';

  @override
  String get profileSignInGoogle => 'Google ile Giriş Yap';

  @override
  String get profileSignOut => 'Çıkış Yap';

  @override
  String get profileBirthdayLabel => 'Doğum Tarihi';

  @override
  String get profileBirthdayNotSet => 'Doğum tarihi ayarlanmadı';

  @override
  String get profileSettingsTitle => 'Ayarlar';

  @override
  String get profileSettingAuthReminders => 'Kimlik Doğrulama Hatırlatıcıları';

  @override
  String get profileSettingAiUpdates => 'Tasarım Önermesi Durum Güncellemeleri';

  @override
  String get authReminderTitle => 'İlerlemenizi kaydetmek için giriş yapın!';

  @override
  String get authReminderBody =>
      'AI tasarımlarınızı kaybetmeyin. Hemen Google ile giriş yapın.';

  @override
  String get authReminderRecurringTitle => 'Mekanlarınız sizi bekliyor';

  @override
  String get authReminderRecurringBody =>
      'AI tasarımlarınızı cihazlar arasında senkronize etmek için giriş yapın.';

  @override
  String get profileSettingLanguage => 'Dil';

  @override
  String get languageEnglish => 'English';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get notificationsTitle => 'Bildirimler';

  @override
  String get noNotificationsMessage => 'Bildirim bulunmuyor';

  @override
  String get noFavoritesMessage =>
      'Henüz favori mobilya yok. Eklemek için ana ekrandaki kalp simgesine dokunun.';
}

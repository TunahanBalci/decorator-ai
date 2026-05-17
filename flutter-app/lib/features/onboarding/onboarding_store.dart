class OnboardingState {
  const OnboardingState({
    this.stage = 0,
    this.decoratingFromScratch,
    this.locationLatitude,
    this.locationLongitude,
    this.ageText = '',
    this.livingSituation,
    this.locationError,
    this.ageError,
  });

  final int stage;
  final bool? decoratingFromScratch;
  final double? locationLatitude;
  final double? locationLongitude;
  final String ageText;
  final String? livingSituation;
  final String? locationError;
  final String? ageError;

  bool get hasLocationInput =>
      locationLatitude != null && locationLongitude != null;

  OnboardingState copyWith({
    int? stage,
    Object? decoratingFromScratch = _unchanged,
    Object? locationLatitude = _unchanged,
    Object? locationLongitude = _unchanged,
    String? ageText,
    Object? livingSituation = _unchanged,
    Object? locationError = _unchanged,
    Object? ageError = _unchanged,
  }) {
    return OnboardingState(
      stage: stage ?? this.stage,
      decoratingFromScratch: decoratingFromScratch == _unchanged
          ? this.decoratingFromScratch
          : decoratingFromScratch as bool?,
      locationLatitude: locationLatitude == _unchanged
          ? this.locationLatitude
          : locationLatitude as double?,
      locationLongitude: locationLongitude == _unchanged
          ? this.locationLongitude
          : locationLongitude as double?,
      ageText: ageText ?? this.ageText,
      livingSituation: livingSituation == _unchanged
          ? this.livingSituation
          : livingSituation as String?,
      locationError: locationError == _unchanged
          ? this.locationError
          : locationError as String?,
      ageError: ageError == _unchanged ? this.ageError : ageError as String?,
    );
  }
}

const _unchanged = Object();

sealed class OnboardingAction {
  const OnboardingAction();
}

class OnboardingPreviousStage extends OnboardingAction {
  const OnboardingPreviousStage();
}

class OnboardingNextStage extends OnboardingAction {
  const OnboardingNextStage();
}

class OnboardingSetDecoratingFromScratch extends OnboardingAction {
  const OnboardingSetDecoratingFromScratch(this.value);

  final bool value;
}

class OnboardingSetLocation extends OnboardingAction {
  const OnboardingSetLocation({
    required this.latitude,
    required this.longitude,
  });

  final double latitude;
  final double longitude;
}

class OnboardingSetAgeText extends OnboardingAction {
  const OnboardingSetAgeText(this.value);

  final String value;
}

class OnboardingSetLivingSituation extends OnboardingAction {
  const OnboardingSetLivingSituation(this.value);

  final String value;
}

class OnboardingSetLocationError extends OnboardingAction {
  const OnboardingSetLocationError(this.value);

  final String? value;
}

class OnboardingSetAgeError extends OnboardingAction {
  const OnboardingSetAgeError(this.value);

  final String? value;
}

OnboardingState onboardingReducer(OnboardingState state, dynamic action) {
  return switch (action) {
    OnboardingPreviousStage() => state.copyWith(
      stage: state.stage == 0 ? 0 : state.stage - 1,
      locationError: null,
      ageError: null,
    ),
    OnboardingNextStage() => state.copyWith(
      stage: state.stage + 1,
      locationError: null,
      ageError: null,
    ),
    OnboardingSetDecoratingFromScratch(value: final value) => state.copyWith(
      decoratingFromScratch: value,
    ),
    OnboardingSetLocation(
      latitude: final latitude,
      longitude: final longitude,
    ) =>
      state.copyWith(
        locationLatitude: latitude,
        locationLongitude: longitude,
        locationError: null,
      ),
    OnboardingSetAgeText(value: final value) => state.copyWith(
      ageText: value,
      ageError: null,
    ),
    OnboardingSetLivingSituation(value: final value) => state.copyWith(
      livingSituation: value,
    ),
    OnboardingSetLocationError(value: final value) => state.copyWith(
      locationError: value,
    ),
    OnboardingSetAgeError(value: final value) => state.copyWith(
      ageError: value,
    ),
    _ => state,
  };
}

import 'dart:async';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'package:redux/redux.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/primary_button.dart';
import '../../l10n/app_localizations.dart';
import '../../navigation/app_shell.dart';
import '../../services/decorator_ai_api.dart';
import '../../services/notification_service.dart';
import 'onboarding_store.dart';

class OnboardingFlowPage extends StatefulWidget {
  const OnboardingFlowPage({
    required this.targetIndex,
    this.homeApi,
    super.key,
  });

  static const decoratingFromScratchKey = 'onboarding_decorating_from_scratch';
  static const locationLatitudeKey = 'onboarding_location_latitude';
  static const locationLongitudeKey = 'onboarding_location_longitude';
  static const ageKey = 'onboarding_age';
  static const livingSituationKey = 'onboarding_living_situation';

  final int targetIndex;
  final DecoratorAiApi? homeApi;

  @override
  State<OnboardingFlowPage> createState() => _OnboardingFlowPageState();
}

class _OnboardingFlowPageState extends State<OnboardingFlowPage> {
  static const _stageCount = 4;
  static const _defaultMapCenter = LatLng(39.9334, 32.8597);

  final _ageController = TextEditingController();
  final _ageFocusNode = FocusNode();
  final _mapController = MapController();

  late final Store<OnboardingState> _store;
  StreamSubscription<OnboardingState>? _storeSubscription;
  bool _isSyncingControllers = false;
  bool _requestedLocation = false;
  bool _isLocating = false;

  OnboardingState get _state => _store.state;

  @override
  void initState() {
    super.initState();
    _store = Store<OnboardingState>(
      onboardingReducer,
      initialState: const OnboardingState(),
    );
    _storeSubscription = _store.onChange.listen((_) {
      _syncControllersFromState();
      if (mounted) setState(() {});
    });

    _ageController.addListener(_handleAgeChanged);
  }

  @override
  void dispose() {
    _storeSubscription?.cancel();
    _ageController.dispose();
    _ageFocusNode.dispose();
    super.dispose();
  }

  void _handleAgeChanged() {
    if (_isSyncingControllers) return;
    _store.dispatch(OnboardingSetAgeText(_ageController.text));
  }

  void _syncControllersFromState() {
    _isSyncingControllers = true;
    _syncController(_ageController, _state.ageText);
    _isSyncingControllers = false;
  }

  void _syncController(TextEditingController controller, String value) {
    if (controller.text == value) return;
    controller.value = TextEditingValue(
      text: value,
      selection: TextSelection.collapsed(offset: value.length),
    );
  }

  void _goBack() {
    if (_state.stage == 0) {
      Navigator.of(context).pop();
      return;
    }

    _store.dispatch(const OnboardingPreviousStage());
    _handleStageEntered();
  }

  Future<void> _goNext() async {
    if (!_validateStage()) return;

    if (_state.stage == _stageCount - 1) {
      await _finish();
      return;
    }

    _store.dispatch(const OnboardingNextStage());
    _handleStageEntered();
  }

  bool _validateStage() {
    final l10n = AppLocalizations.of(context)!;

    if (_state.stage == 2) {
      final ageText = _state.ageText.trim();
      if (ageText.isNotEmpty) {
        final age = int.tryParse(ageText);
        if (age == null || age < 13 || age > 120) {
          _store.dispatch(OnboardingSetAgeError(l10n.onboardingAgeInvalid));
          return false;
        }
      }
    }

    return true;
  }

  Future<void> _finish() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AppShell.enteredAppKey, true);
    await prefs.setInt(AppShell.selectedTabKey, widget.targetIndex);

    final decorating = _state.decoratingFromScratch;
    if (decorating != null) {
      await prefs.setBool(
        OnboardingFlowPage.decoratingFromScratchKey,
        decorating,
      );
    }

    if (_state.hasLocationInput) {
      await prefs.setDouble(
        OnboardingFlowPage.locationLatitudeKey,
        _state.locationLatitude!,
      );
      await prefs.setDouble(
        OnboardingFlowPage.locationLongitudeKey,
        _state.locationLongitude!,
      );
    }

    final age = int.tryParse(_state.ageText.trim());
    if (age != null) await prefs.setInt(OnboardingFlowPage.ageKey, age);

    final livingSituation = _state.livingSituation;
    if (livingSituation != null) {
      await prefs.setString(
        OnboardingFlowPage.livingSituationKey,
        livingSituation,
      );
    }

    try {
      await FirebaseFirestore.instanceFor(app: Firebase.app(), databaseId: 'default').collection('onboarding_responses').add({
        'decoratingFromScratch': _state.decoratingFromScratch,
        'locationLatitude': _state.locationLatitude,
        'locationLongitude': _state.locationLongitude,
        'age': int.tryParse(_state.ageText.trim()),
        'livingSituation': _state.livingSituation,
        'timestamp': FieldValue.serverTimestamp(),
      });
    } catch (_) {
      // Proceed even if database storage fails
    }

    if (!mounted) return;
    
    final l10n = AppLocalizations.of(context)!;
    try {
      if (FirebaseAuth.instance.currentUser == null) {
        await NotificationService.instance.scheduleOnboardingReminders(
          l10n.authReminderTitle,
          l10n.authReminderBody,
          l10n.authReminderRecurringTitle,
          l10n.authReminderRecurringBody,
        );
      }
    } catch (_) {}

    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) =>
            AppShell(initialIndex: widget.targetIndex, homeApi: widget.homeApi),
      ),
      (route) => false,
    );
  }

  bool get _hasInput {
    return switch (_state.stage) {
      0 => _state.decoratingFromScratch != null,
      1 => _state.hasLocationInput,
      2 => _state.ageText.trim().isNotEmpty,
      3 => _state.livingSituation != null,
      _ => false,
    };
  }

  void _handleStageEntered() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (_state.stage == 1 && !_requestedLocation) {
        unawaited(_centerOnUserLocation());
      }
      if (_state.stage == 2) _ageFocusNode.requestFocus();
    });
  }

  void _selectLocation(LatLng point) {
    _store.dispatch(
      OnboardingSetLocation(
        latitude: point.latitude,
        longitude: point.longitude,
      ),
    );
  }

  Future<void> _centerOnUserLocation() async {
    final l10n = AppLocalizations.of(context)!;

    setState(() {
      _requestedLocation = true;
      _isLocating = true;
    });

    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _store.dispatch(
          OnboardingSetLocationError(l10n.onboardingLocationServiceDisabled),
        );
        return;
      }

      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      if (permission == LocationPermission.denied) {
        _store.dispatch(
          OnboardingSetLocationError(l10n.onboardingLocationPermissionDenied),
        );
        return;
      }

      if (permission == LocationPermission.deniedForever) {
        _store.dispatch(
          OnboardingSetLocationError(
            l10n.onboardingLocationPermissionDeniedForever,
          ),
        );
        return;
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      );
      final point = LatLng(position.latitude, position.longitude);
      _selectLocation(point);
      _mapController.move(point, 15);
    } on MissingPluginException {
      // Widget tests do not register the native location plugin.
    } catch (_) {
      _store.dispatch(
        OnboardingSetLocationError(l10n.onboardingLocationUnavailable),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLocating = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 430),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(22, 16, 22, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _OnboardingHeader(
                    currentStage: _state.stage,
                    stageCount: _stageCount,
                    onBack: _goBack,
                  ),
                  const SizedBox(height: 28),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(999),
                    child: LinearProgressIndicator(
                      value: (_state.stage + 1) / _stageCount,
                      minHeight: 6,
                      backgroundColor: AppColors.border,
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        AppColors.ink,
                      ),
                    ),
                  ),
                  const SizedBox(height: 42),
                  Expanded(
                    child: SingleChildScrollView(
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: 18),
                        child: _buildStage(l10n),
                      ),
                    ),
                  ),
                  PrimaryButton(
                    label: _hasInput
                        ? l10n.onboardingNext
                        : l10n.onboardingSkip,
                    icon: _hasInput
                        ? Icons.arrow_forward_rounded
                        : Icons.skip_next_rounded,
                    onPressed: _goNext,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStage(AppLocalizations l10n) {
    return switch (_state.stage) {
      0 => _ChoiceStage<bool>(
        title: l10n.onboardingScratchQuestion,
        subtitle: l10n.onboardingOptionalSubtitle,
        value: _state.decoratingFromScratch,
        options: [
          _ChoiceOption(value: true, label: l10n.onboardingYes),
          _ChoiceOption(value: false, label: l10n.onboardingNo),
        ],
        onChanged: (value) {
          _store.dispatch(OnboardingSetDecoratingFromScratch(value));
        },
      ),
      1 => _LocationStage(
        state: _state,
        mapController: _mapController,
        defaultCenter: _defaultMapCenter,
        isLocating: _isLocating,
        onLocationSelected: _selectLocation,
        onUseCurrentLocation: _centerOnUserLocation,
      ),
      2 => _AgeStage(
        controller: _ageController,
        focusNode: _ageFocusNode,
        errorText: _state.ageError,
      ),
      3 => _ChoiceStage<String>(
        title: l10n.onboardingLivingQuestion,
        subtitle: l10n.onboardingOptionalSubtitle,
        value: _state.livingSituation,
        options: [
          _ChoiceOption(value: 'alone', label: l10n.onboardingLivingAlone),
          _ChoiceOption(value: 'family', label: l10n.onboardingLivingFamily),
        ],
        onChanged: (value) {
          _store.dispatch(OnboardingSetLivingSituation(value));
        },
      ),
      _ => const SizedBox.shrink(),
    };
  }
}

class _OnboardingHeader extends StatelessWidget {
  const _OnboardingHeader({
    required this.currentStage,
    required this.stageCount,
    required this.onBack,
  });

  final int currentStage;
  final int stageCount;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Row(
      children: [
        IconButton.filled(
          onPressed: onBack,
          icon: const Icon(Icons.arrow_back_rounded),
          style: IconButton.styleFrom(
            backgroundColor: AppColors.surface,
            foregroundColor: AppColors.ink,
          ),
        ),
        const Spacer(),
        Text(
          l10n.onboardingStep(currentStage + 1, stageCount),
          style: const TextStyle(
            color: AppColors.muted,
            fontSize: 13,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}

class _ChoiceStage<T> extends StatelessWidget {
  const _ChoiceStage({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.options,
    required this.onChanged,
  });

  final String title;
  final String subtitle;
  final T? value;
  final List<_ChoiceOption<T>> options;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _StageTitle(title: title, subtitle: subtitle),
        const SizedBox(height: 28),
        ...options.map((option) {
          return _ChoiceTile(
            label: option.label,
            selected: option.value == value,
            onTap: () => onChanged(option.value),
          );
        }),
      ],
    );
  }
}

class _ChoiceOption<T> {
  const _ChoiceOption({required this.value, required this.label});

  final T value;
  final String label;
}

class _ChoiceTile extends StatelessWidget {
  const _ChoiceTile({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Material(
        color: selected ? AppColors.ink : AppColors.surface,
        borderRadius: BorderRadius.circular(24),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
            decoration: BoxDecoration(
              border: Border.all(
                color: selected ? AppColors.ink : AppColors.border,
              ),
              borderRadius: BorderRadius.circular(24),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    label,
                    style: TextStyle(
                      color: selected ? Colors.white : AppColors.ink,
                      fontSize: 17,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Icon(
                  selected ? Icons.check_circle_rounded : Icons.circle_outlined,
                  color: selected ? Colors.white : AppColors.muted,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LocationStage extends StatelessWidget {
  const _LocationStage({
    required this.state,
    required this.mapController,
    required this.defaultCenter,
    required this.isLocating,
    required this.onLocationSelected,
    required this.onUseCurrentLocation,
  });

  final OnboardingState state;
  final MapController mapController;
  final LatLng defaultCenter;
  final bool isLocating;
  final ValueChanged<LatLng> onLocationSelected;
  final VoidCallback onUseCurrentLocation;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final selectedLocation =
        state.locationLatitude == null || state.locationLongitude == null
        ? null
        : LatLng(state.locationLatitude!, state.locationLongitude!);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _StageTitle(
          title: l10n.onboardingLocationQuestion,
          subtitle: l10n.onboardingLocationSubtitle,
        ),
        const SizedBox(height: 28),
        DecoratedBox(
          decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(24),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: SizedBox(
              key: const ValueKey('onboarding-location-map'),
              height: 360,
              child: Stack(
                children: [
                  FlutterMap(
                    mapController: mapController,
                    options: MapOptions(
                      initialCenter: selectedLocation ?? defaultCenter,
                      initialZoom: selectedLocation == null ? 11 : 15,
                      onTap: (_, point) => onLocationSelected(point),
                    ),
                    children: [
                      TileLayer(
                        urlTemplate:
                            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'decorator_ai',
                      ),
                      if (selectedLocation != null)
                        MarkerLayer(
                          markers: [
                            Marker(
                              point: selectedLocation,
                              width: 44,
                              height: 44,
                              child: const _MapPin(),
                            ),
                          ],
                        ),
                    ],
                  ),
                  Center(
                    child: Tooltip(
                      message: l10n.onboardingSelectMapCenter,
                      child: IconButton.filled(
                        key: const ValueKey('onboarding-select-map-center'),
                        onPressed: () {
                          onLocationSelected(mapController.camera.center);
                        },
                        icon: const Icon(Icons.add_location_alt_rounded),
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: AppColors.ink,
                          shadowColor: Colors.black.withValues(alpha: 0.18),
                          elevation: 3,
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    top: 14,
                    right: 14,
                    child: FilledButton.icon(
                      onPressed: isLocating ? null : onUseCurrentLocation,
                      icon: isLocating
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.my_location_rounded, size: 18),
                      label: Text(l10n.onboardingUseCurrentLocation),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.ink,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 10,
                        ),
                        textStyle: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    left: 14,
                    right: 14,
                    bottom: 14,
                    child: _MapStatusCard(
                      selectedLocation: selectedLocation,
                      errorText: state.locationError,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _MapStatusCard extends StatelessWidget {
  const _MapStatusCard({
    required this.selectedLocation,
    required this.errorText,
  });

  final LatLng? selectedLocation;
  final String? errorText;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final text = errorText != null
        ? errorText!
        : selectedLocation == null
        ? l10n.onboardingLocationMapHint
        : l10n.onboardingLocationSelected(
            selectedLocation!.latitude.toStringAsFixed(5),
            selectedLocation!.longitude.toStringAsFixed(5),
          );

    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.94),
        border: Border.all(
          color: errorText == null ? AppColors.border : const Color(0xFFD44A4A),
        ),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Icon(
              errorText == null
                  ? Icons.location_on_rounded
                  : Icons.info_outline_rounded,
              color: errorText == null
                  ? AppColors.ink
                  : const Color(0xFFD44A4A),
              size: 20,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                text,
                style: TextStyle(
                  color: errorText == null
                      ? AppColors.ink
                      : const Color(0xFFD44A4A),
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MapPin extends StatelessWidget {
  const _MapPin();

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: AppColors.ink.withValues(alpha: 0.18),
            shape: BoxShape.circle,
          ),
        ),
        const Icon(Icons.location_on_rounded, color: AppColors.ink, size: 38),
      ],
    );
  }
}

class _AgeStage extends StatelessWidget {
  const _AgeStage({
    required this.controller,
    required this.focusNode,
    required this.errorText,
  });

  final TextEditingController controller;
  final FocusNode focusNode;
  final String? errorText;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (context.mounted) focusNode.requestFocus();
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _StageTitle(
          title: l10n.onboardingAgeQuestion,
          subtitle: l10n.onboardingOptionalSubtitle,
        ),
        const SizedBox(height: 28),
        _OnboardingTextField(
          fieldKey: const ValueKey('onboarding-age-field'),
          controller: controller,
          focusNode: focusNode,
          label: l10n.onboardingAgeLabel,
          hintText: l10n.onboardingAgeHint,
          errorText: errorText,
          keyboardType: TextInputType.number,
          textInputAction: TextInputAction.done,
          inputFormatters: [FilteringTextInputFormatter.digitsOnly],
        ),
      ],
    );
  }
}

class _StageTitle extends StatelessWidget {
  const _StageTitle({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.headlineLarge),
        const SizedBox(height: 14),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }
}

class _OnboardingTextField extends StatelessWidget {
  const _OnboardingTextField({
    required this.controller,
    required this.fieldKey,
    required this.focusNode,
    required this.label,
    required this.hintText,
    this.errorText,
    this.keyboardType,
    this.textInputAction,
    this.inputFormatters,
  });

  final TextEditingController controller;
  final Key fieldKey;
  final FocusNode focusNode;
  final String label;
  final String hintText;
  final String? errorText;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final List<TextInputFormatter>? inputFormatters;

  @override
  Widget build(BuildContext context) {
    return TextField(
      key: fieldKey,
      controller: controller,
      focusNode: focusNode,
      autofocus: true,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      inputFormatters: inputFormatters,
      style: const TextStyle(
        color: AppColors.ink,
        fontSize: 20,
        fontWeight: FontWeight.w800,
      ),
      decoration: InputDecoration(
        labelText: label,
        hintText: hintText,
        errorText: errorText,
        filled: true,
        fillColor: AppColors.surface,
        labelStyle: const TextStyle(
          color: AppColors.muted,
          fontWeight: FontWeight.w700,
        ),
        hintStyle: const TextStyle(color: AppColors.muted),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(22),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        disabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(22),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(22),
          borderSide: const BorderSide(color: AppColors.ink, width: 1.4),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(22),
          borderSide: const BorderSide(color: Color(0xFFD44A4A)),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(22),
          borderSide: const BorderSide(color: Color(0xFFD44A4A), width: 1.4),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/primary_button.dart';
import '../../l10n/app_localizations.dart';
import '../../navigation/app_shell.dart';
import '../../services/decorator_ai_api.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({required this.targetIndex, this.homeApi, super.key});

  static const decoratingFromScratchKey = 'onboarding_decorating_from_scratch';
  static const cityKey = 'onboarding_city';
  static const ageKey = 'onboarding_age';
  static const livingSituationKey = 'onboarding_living_situation';

  final int targetIndex;
  final DecoratorAiApi? homeApi;

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  static const _stageCount = 4;

  final _cityController = TextEditingController();
  final _ageController = TextEditingController();
  final _cityFocusNode = FocusNode();
  final _ageFocusNode = FocusNode();

  int _stage = 0;
  bool? _decoratingFromScratch;
  String? _livingSituation;
  String? _cityError;
  String? _ageError;

  @override
  void initState() {
    super.initState();
    _cityController.addListener(_handleTextChanged);
    _ageController.addListener(_handleTextChanged);
  }

  @override
  void dispose() {
    _cityController.dispose();
    _ageController.dispose();
    _cityFocusNode.dispose();
    _ageFocusNode.dispose();
    super.dispose();
  }

  void _handleTextChanged() {
    setState(() {
      _cityError = null;
      _ageError = null;
    });
  }

  void _goBack() {
    if (_stage == 0) {
      Navigator.of(context).pop();
      return;
    }

    setState(() => _stage -= 1);
    _focusCurrentTextInput();
  }

  Future<void> _goNext() async {
    if (!_validateStage()) return;

    if (_stage == _stageCount - 1) {
      await _finish();
      return;
    }

    setState(() => _stage += 1);
    _focusCurrentTextInput();
  }

  bool _validateStage() {
    final l10n = AppLocalizations.of(context)!;

    if (_stage == 1) {
      final city = _cityController.text.trim();
      if (city.isNotEmpty && !_isKnownCity(city)) {
        setState(() => _cityError = l10n.onboardingCityInvalid);
        return false;
      }
    }

    if (_stage == 2) {
      final ageText = _ageController.text.trim();
      if (ageText.isNotEmpty) {
        final age = int.tryParse(ageText);
        if (age == null || age < 16 || age > 120) {
          setState(() => _ageError = l10n.onboardingAgeInvalid);
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

    final decorating = _decoratingFromScratch;
    if (decorating != null) {
      await prefs.setBool(OnboardingPage.decoratingFromScratchKey, decorating);
    }

    final city = _cityController.text.trim();
    if (city.isNotEmpty) {
      await prefs.setString(OnboardingPage.cityKey, _canonicalCity(city));
    }

    final age = int.tryParse(_ageController.text.trim());
    if (age != null) await prefs.setInt(OnboardingPage.ageKey, age);

    final livingSituation = _livingSituation;
    if (livingSituation != null) {
      await prefs.setString(OnboardingPage.livingSituationKey, livingSituation);
    }

    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) =>
            AppShell(initialIndex: widget.targetIndex, homeApi: widget.homeApi),
      ),
    );
  }

  bool get _hasInput {
    return switch (_stage) {
      0 => _decoratingFromScratch != null,
      1 => _cityController.text.trim().isNotEmpty,
      2 => _ageController.text.trim().isNotEmpty,
      3 => _livingSituation != null,
      _ => false,
    };
  }

  void _focusCurrentTextInput() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (_stage == 1) _cityFocusNode.requestFocus();
      if (_stage == 2) _ageFocusNode.requestFocus();
    });
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
                    currentStage: _stage,
                    stageCount: _stageCount,
                    onBack: _goBack,
                  ),
                  const SizedBox(height: 28),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(999),
                    child: LinearProgressIndicator(
                      value: (_stage + 1) / _stageCount,
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
    return switch (_stage) {
      0 => _ChoiceStage<bool>(
        title: l10n.onboardingScratchQuestion,
        subtitle: l10n.onboardingOptionalSubtitle,
        value: _decoratingFromScratch,
        options: [
          _ChoiceOption(value: true, label: l10n.onboardingYes),
          _ChoiceOption(value: false, label: l10n.onboardingNo),
        ],
        onChanged: (value) => setState(() => _decoratingFromScratch = value),
      ),
      1 => _CityStage(
        controller: _cityController,
        focusNode: _cityFocusNode,
        errorText: _cityError,
      ),
      2 => _AgeStage(
        controller: _ageController,
        focusNode: _ageFocusNode,
        errorText: _ageError,
      ),
      3 => _ChoiceStage<String>(
        title: l10n.onboardingLivingQuestion,
        subtitle: l10n.onboardingOptionalSubtitle,
        value: _livingSituation,
        options: [
          _ChoiceOption(value: 'alone', label: l10n.onboardingLivingAlone),
          _ChoiceOption(value: 'family', label: l10n.onboardingLivingFamily),
        ],
        onChanged: (value) => setState(() => _livingSituation = value),
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

class _CityStage extends StatelessWidget {
  const _CityStage({
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _StageTitle(
          title: l10n.onboardingCityQuestion,
          subtitle: l10n.onboardingCitySubtitle,
        ),
        const SizedBox(height: 28),
        RawAutocomplete<String>(
          textEditingController: controller,
          focusNode: focusNode,
          optionsBuilder: (value) {
            final query = value.text.trim().toLowerCase();
            if (query.isEmpty) return const Iterable<String>.empty();

            return _worldCities
                .where((city) {
                  return city.toLowerCase().contains(query);
                })
                .take(8);
          },
          onSelected: (city) => controller.text = city,
          fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (context.mounted) focusNode.requestFocus();
            });

            return _OnboardingTextField(
              controller: controller,
              focusNode: focusNode,
              label: l10n.onboardingCityLabel,
              hintText: l10n.onboardingCityHint,
              errorText: errorText,
              textInputAction: TextInputAction.next,
              onSubmitted: (_) => onSubmitted(),
            );
          },
          optionsViewBuilder: (context, onSelected, options) {
            return Align(
              alignment: Alignment.topLeft,
              child: Material(
                color: AppColors.surface,
                elevation: 8,
                borderRadius: BorderRadius.circular(18),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 250),
                  child: ListView.builder(
                    padding: EdgeInsets.zero,
                    shrinkWrap: true,
                    itemCount: options.length,
                    itemBuilder: (context, index) {
                      final option = options.elementAt(index);
                      return ListTile(
                        title: Text(
                          option,
                          style: const TextStyle(
                            color: AppColors.ink,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        onTap: () => onSelected(option),
                      );
                    },
                  ),
                ),
              ),
            );
          },
        ),
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
    required this.focusNode,
    required this.label,
    required this.hintText,
    this.errorText,
    this.keyboardType,
    this.textInputAction,
    this.inputFormatters,
    this.onSubmitted,
  });

  final TextEditingController controller;
  final FocusNode focusNode;
  final String label;
  final String hintText;
  final String? errorText;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final List<TextInputFormatter>? inputFormatters;
  final ValueChanged<String>? onSubmitted;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      focusNode: focusNode,
      autofocus: true,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      inputFormatters: inputFormatters,
      onSubmitted: onSubmitted,
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

bool _isKnownCity(String value) {
  return _worldCities.any((city) => city.toLowerCase() == value.toLowerCase());
}

String _canonicalCity(String value) {
  return _worldCities.firstWhere(
    (city) => city.toLowerCase() == value.toLowerCase(),
    orElse: () => value,
  );
}

const _worldCities = [
  'Amsterdam',
  'Ankara',
  'Antalya',
  'Athens',
  'Atlanta',
  'Auckland',
  'Bangkok',
  'Barcelona',
  'Beijing',
  'Berlin',
  'Bogota',
  'Boston',
  'Brussels',
  'Buenos Aires',
  'Cairo',
  'Cape Town',
  'Chicago',
  'Copenhagen',
  'Dallas',
  'Delhi',
  'Doha',
  'Dubai',
  'Dublin',
  'Frankfurt',
  'Geneva',
  'Hamburg',
  'Hong Kong',
  'Houston',
  'Istanbul',
  'Izmir',
  'Jakarta',
  'Johannesburg',
  'Kuala Lumpur',
  'Kyoto',
  'Lisbon',
  'London',
  'Los Angeles',
  'Madrid',
  'Manchester',
  'Melbourne',
  'Mexico City',
  'Miami',
  'Milan',
  'Montreal',
  'Moscow',
  'Mumbai',
  'Munich',
  'New York',
  'Osaka',
  'Oslo',
  'Paris',
  'Prague',
  'Rio de Janeiro',
  'Rome',
  'San Francisco',
  'Santiago',
  'Sao Paulo',
  'Seoul',
  'Shanghai',
  'Singapore',
  'Stockholm',
  'Sydney',
  'Taipei',
  'Tokyo',
  'Toronto',
  'Vancouver',
  'Vienna',
  'Warsaw',
  'Zurich',
];

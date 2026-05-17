import 'package:flutter/material.dart';
import '../../core/widgets/primary_button.dart';
import '../../core/widgets/remote_image.dart';
import '../../features/onboarding/onboarding_flow_page.dart';
import '../../l10n/app_localizations.dart';
import '../../services/decorator_ai_api.dart';

class WelcomePage extends StatelessWidget {
  const WelcomePage({this.homeApi, super.key});

  final DecoratorAiApi? homeApi;

  void _openOnboarding(BuildContext context, {int targetIndex = 0}) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            OnboardingFlowPage(targetIndex: targetIndex, homeApi: homeApi),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 22, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.asset(
                      'assets/app_logo_trimmed.png',
                      width: 50,
                      height: 50,
                      fit: BoxFit.cover,
                      filterQuality: FilterQuality.high,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    l10n.appBrand,
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900),
                  ),
                ],
              ),
              const SizedBox(height: 28),
              Text(
                l10n.welcomeHeadline,
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(height: 16),
              Text(
                l10n.welcomeSubtitle,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 26),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(34),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      const RemoteImage(
                        url:
                            'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=80',
                        fit: BoxFit.cover,
                      ),
                      const DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [Colors.transparent, Colors.black54],
                          ),
                        ),
                      ),
                      Positioned(
                        left: 18,
                        right: 18,
                        bottom: 18,
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.90),
                            borderRadius: BorderRadius.circular(22),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.auto_awesome_rounded),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  l10n.welcomeInsight,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    height: 1.25,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              PrimaryButton(
                label: l10n.welcomeStartScan,
                icon: Icons.document_scanner_rounded,
                onPressed: () => _openOnboarding(context, targetIndex: 1),
              ),
              const SizedBox(height: 12),
              PrimaryButton(
                label: l10n.welcomeExploreExamples,
                icon: Icons.grid_view_rounded,
                isOutlined: true,
                onPressed: () => _openOnboarding(context),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/remote_image.dart';
import '../../data/sample_furniture.dart';
import '../../l10n/app_localizations.dart';
import '../../models/design_project.dart';
import '../../models/furniture_item.dart';
import '../../models/product_spot.dart';
import '../../services/decorator_ai_api.dart';
import '../design/design_detail_page.dart';
import '../product/product_detail_page.dart';
import '../notifications/notifications_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({
    required this.favoriteIds,
    required this.onToggleFavorite,
    required this.onOpenScan,
    this.api,
    super.key,
  });

  final Set<String> favoriteIds;
  final ValueChanged<String> onToggleFavorite;
  final VoidCallback onOpenScan;
  final DecoratorAiApi? api;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late final DecoratorAiApi _api = widget.api ?? FirestoreDecoratorAiApi();
  late final Future<List<DesignProject>> _projects = _api.fetchProjects();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return SafeArea(
      child: FutureBuilder<List<DesignProject>>(
        future: _projects,
        builder: (context, snapshot) {
          final projects = snapshot.data ?? const <DesignProject>[];

          return ListView(
            padding: const EdgeInsets.fromLTRB(22, 22, 22, 116),
            children: [
              Row(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(14),
                    child: Image.asset(
                      'assets/app_logo_trimmed.png',
                      width: 46,
                      height: 46,
                      fit: BoxFit.cover,
                      filterQuality: FilterQuality.high,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l10n.appBrand,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        Text(
                          l10n.homeSubtitle,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  IconButton.filled(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const NotificationsPage(),
                        ),
                      );
                    },
                    icon: const Icon(Icons.notifications_none_rounded),
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.surface,
                      foregroundColor: AppColors.ink,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 28),
              _NewScanCard(
                badge: l10n.homeNewScanBadge,
                title: l10n.homeHeroTitle,
                body: l10n.homeHeroBody,
                onTap: widget.onOpenScan,
              ),
              const SizedBox(height: 26),
              Text(
                'Example Furniture',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 14),
              ...sampleFurniture.map((item) {
                return _FurnitureCard(
                  item: item,
                  isFavorite: widget.favoriteIds.contains(item.id),
                  onToggleFavorite: () => widget.onToggleFavorite(item.id),
                );
              }),
              const SizedBox(height: 10),
              Text(
                l10n.homeSuggestionsTitle,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 14),
              if (snapshot.connectionState == ConnectionState.waiting)
                const Center(child: CircularProgressIndicator())
              else
                ...projects.map((project) {
                  return _ProjectCard(project: project);
                }),
            ],
          );
        },
      ),
    );
  }
}

class _NewScanCard extends StatefulWidget {
  const _NewScanCard({
    required this.badge,
    required this.title,
    required this.body,
    required this.onTap,
  });

  final String badge;
  final String title;
  final String body;
  final VoidCallback onTap;

  @override
  State<_NewScanCard> createState() => _NewScanCardState();
}

class _NewScanCardState extends State<_NewScanCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (context, child) {
                final progress = Curves.easeOut.transform(
                  _pulseController.value,
                );

                return Opacity(
                  opacity: 0.42 * (1 - progress),
                  child: Transform.scale(
                    scale: 1 + (progress * 0.045),
                    child: child,
                  ),
                );
              },
              child: DecoratedBox(
                decoration: BoxDecoration(
                  border: Border.all(
                    color: AppColors.ink.withValues(alpha: 0.65),
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(30),
                ),
              ),
            ),
          ),
          Material(
            color: AppColors.ink,
            borderRadius: BorderRadius.circular(30),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: widget.onTap,
              child: Padding(
                padding: const EdgeInsets.all(22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 8,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white12,
                            borderRadius: BorderRadius.circular(30),
                          ),
                          child: Text(
                            widget.badge,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        const Spacer(),
                        Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.white24),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.arrow_forward_rounded,
                            color: Colors.white,
                            size: 22,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 22),
                    Text(
                      widget.title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        height: 1.1,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      widget.body,
                      style: const TextStyle(
                        color: Colors.white70,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FurnitureCard extends StatelessWidget {
  const _FurnitureCard({
    required this.item,
    required this.isFavorite,
    required this.onToggleFavorite,
  });

  final FurnitureItem item;
  final bool isFavorite;
  final VoidCallback onToggleFavorite;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.07),
            blurRadius: 20,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(24),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => ProductDetailPage(
                  product: ProductSpot(
                    id: item.id,
                    name: item.title,
                    brand: item.material,
                    price: 'Ask for price',
                    matchScore: 99,
                    left: 0,
                    top: 0,
                    imageUrl: item.imageUrl,
                    buyUrl: '',
                  ),
                  isFavorite: isFavorite,
                  onToggleFavorite: onToggleFavorite,
                ),
              ),
            );
          },
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
          AspectRatio(
            aspectRatio: 1.65,
            child: Stack(
              fit: StackFit.expand,
              children: [
                RemoteImage(url: item.imageUrl),
                Positioned(
                  top: 12,
                  right: 12,
                  child: _CardActionButton(
                    icon: isFavorite
                        ? Icons.favorite_rounded
                        : Icons.favorite_border_rounded,
                    foregroundColor: isFavorite
                        ? const Color(0xFFE84D7A)
                        : AppColors.ink,
                    onPressed: onToggleFavorite,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        item.title,
                        style: const TextStyle(
                          color: AppColors.ink,
                          fontSize: 19,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(30),
                      ),
                      child: Text(
                        item.category,
                        style: const TextStyle(
                          color: AppColors.ink,
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  item.description,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Icon(Icons.category_rounded, size: 17),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        '${item.category} / ${item.material}',
                        style: const TextStyle(
                          color: AppColors.muted,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  ),
);
  }
}

class _CardActionButton extends StatelessWidget {
  const _CardActionButton({
    required this.icon,
    required this.foregroundColor,
    required this.onPressed,
  });

  final IconData icon;
  final Color foregroundColor;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 44,
      height: 44,
      child: IconButton.filled(
        padding: EdgeInsets.zero,
        onPressed: onPressed,
        icon: Icon(icon),
        style: IconButton.styleFrom(
          backgroundColor: Colors.white,
          foregroundColor: foregroundColor,
          shadowColor: Colors.black26,
          elevation: 3,
        ),
      ),
    );
  }
}

class _ProjectCard extends StatelessWidget {
  const _ProjectCard({required this.project});

  final DesignProject project;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        borderRadius: BorderRadius.circular(28),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => DesignDetailPage(project: project),
            ),
          );
        },
        child: Container(
          height: 250,
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(28),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.08),
                blurRadius: 22,
                offset: const Offset(0, 12),
              ),
            ],
          ),
          clipBehavior: Clip.antiAlias,
          child: Stack(
            fit: StackFit.expand,
            children: [
              RemoteImage(url: project.imageUrl),
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.transparent, Colors.black87],
                  ),
                ),
              ),
              Positioned(
                left: 18,
                right: 18,
                bottom: 18,
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            project.title,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 7),
                          Text(
                            '${project.spaceType} • ${project.style}',
                            style: const TextStyle(color: Colors.white70),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.arrow_forward_rounded),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

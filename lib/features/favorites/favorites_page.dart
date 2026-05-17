import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/remote_image.dart';
import '../../data/sample_furniture.dart';
import '../../l10n/app_localizations.dart';
import '../../models/furniture_item.dart';
import '../../models/product_spot.dart';
import '../product/product_detail_page.dart';

class FavoritesPage extends StatelessWidget {
  const FavoritesPage({
    required this.favoriteIds,
    required this.onToggleFavorite,
    super.key,
  });

  final Set<String> favoriteIds;
  final ValueChanged<String> onToggleFavorite;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final favorites = sampleFurniture
        .where((item) => favoriteIds.contains(item.id))
        .toList();

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(22, 24, 22, 116),
        children: [
          Row(
            children: [
              const Icon(Icons.favorite_rounded, color: Color(0xFFE84D7A)),
              const SizedBox(width: 10),
              Text(
                l10n.savedTitle,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            l10n.savedSubtitle,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 20),
          if (favorites.isEmpty)
            Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: AppColors.border),
              ),
              child: Text(
                l10n.noFavoritesMessage,
                style: const TextStyle(color: AppColors.muted, height: 1.4),
              ),
            )
          else
            for (final item in favorites)
              _FavoriteFurnitureTile(
                item: item,
                onToggleFavorite: () => onToggleFavorite(item.id),
              ),
        ],
      ),
    );
  }
}

class _FavoriteFurnitureTile extends StatelessWidget {
  const _FavoriteFurnitureTile({
    required this.item,
    required this.onToggleFavorite,
  });

  final FurnitureItem item;
  final VoidCallback onToggleFavorite;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 18,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Material(
        color: AppColors.surface,
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
                  isFavorite: true,
                  onToggleFavorite: onToggleFavorite,
                ),
              ),
            );
          },
          child: Row(
            children: [
              RemoteImage(url: item.imageUrl, width: 104, height: 120),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.title,
                        style: const TextStyle(
                          color: AppColors.ink,
                          fontWeight: FontWeight.w900,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        '${item.category} / ${item.material}',
                        style: const TextStyle(
                          color: AppColors.muted,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          _RoundIconButton(
                            icon: Icons.favorite_rounded,
                            color: const Color(0xFFE84D7A),
                            onPressed: onToggleFavorite,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoundIconButton extends StatelessWidget {
  const _RoundIconButton({
    required this.icon,
    required this.color,
    required this.onPressed,
  });

  final IconData icon;
  final Color color;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 40,
      height: 40,
      child: IconButton.filled(
        padding: EdgeInsets.zero,
        onPressed: onPressed,
        icon: Icon(icon, size: 20),
        style: IconButton.styleFrom(
          backgroundColor: AppColors.background,
          foregroundColor: color,
        ),
      ),
    );
  }
}

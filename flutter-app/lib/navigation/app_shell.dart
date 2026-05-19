import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/theme/app_colors.dart';
import '../features/favorites/favorites_page.dart';
import '../features/home/home_page.dart';
import '../features/profile/profile_page.dart';
import '../features/scan/scan_page.dart';
import '../l10n/app_localizations.dart';
import '../services/app_notification_service.dart';
import '../services/decorator_ai_api.dart';
import '../services/product_favorite_service.dart';

class AppShell extends StatefulWidget {
  const AppShell({this.initialIndex = 0, this.homeApi, super.key});

  static const enteredAppKey = 'has_entered_app';
  static const selectedTabKey = 'selected_tab_index';

  final int initialIndex;
  final DecoratorAiApi? homeApi;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  late int _index;
  Set<String> _favoriteFurnitureIds = <String>{};

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex.clamp(0, 3).toInt();
    _persistSelectedIndex(_index);
    _loadFurnitureState();
    AppNotificationService.instance.loadNotifications();
  }

  Future<void> _loadFurnitureState() async {
    final favorites = await ProductFavoriteService.instance.loadFavorites();
    if (!mounted) return;

    setState(() {
      _favoriteFurnitureIds = favorites;
    });
  }

  Future<void> _persistSelectedIndex(int index) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AppShell.enteredAppKey, true);
    await prefs.setInt(AppShell.selectedTabKey, index);
  }

  void _selectIndex(int index) {
    setState(() => _index = index);
    _persistSelectedIndex(index);
  }

  void _toggleFavorite(String furnitureId) {
    ProductFavoriteService.instance.toggleFavorite(furnitureId).then((_) {
      if (!mounted) return;
      setState(() {
        _favoriteFurnitureIds =
            ProductFavoriteService.instance.favoriteIds.value;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final pages = [
      HomePage(
        favoriteIds: _favoriteFurnitureIds,
        onToggleFavorite: _toggleFavorite,
        onOpenScan: () => _selectIndex(1),
        api: widget.homeApi,
      ),
      const ScanPage(),
      FavoritesPage(
        favoriteIds: _favoriteFurnitureIds,
        onToggleFavorite: _toggleFavorite,
      ),
      const ProfilePage(),
    ];

    return Scaffold(
      body: Stack(
        children: [
          IndexedStack(index: _index, children: pages),
          Positioned(
            left: 18,
            right: 18,
            bottom: 16,
            child: SafeArea(
              child: Container(
                height: 74,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.surface.withValues(alpha: 0.96),
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.ink.withValues(alpha: 0.10),
                      blurRadius: 26,
                      offset: const Offset(0, 14),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _NavItem(
                      icon: Icons.home_rounded,
                      label: l10n.navHome,
                      selected: _index == 0,
                      onTap: () => _selectIndex(0),
                    ),
                    _NavItem(
                      icon: Icons.document_scanner_rounded,
                      label: l10n.navScan,
                      selected: _index == 1,
                      onTap: () => _selectIndex(1),
                    ),
                    _NavItem(
                      icon: Icons.favorite_rounded,
                      label: l10n.navSaved,
                      selected: _index == 2,
                      onTap: () => _selectIndex(2),
                    ),
                    _NavItem(
                      icon: Icons.person_rounded,
                      label: l10n.navProfile,
                      selected: _index == 3,
                      onTap: () => _selectIndex(3),
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

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          height: 58,
          decoration: BoxDecoration(
            color: selected
                ? AppColors.sage
                : AppColors.sage.withValues(alpha: 0.00),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 21,
                color: selected ? Colors.white : AppColors.muted,
              ),
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 3),
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    label,
                    maxLines: 1,
                    style: TextStyle(
                      color: selected ? Colors.white : AppColors.muted,
                      fontSize: 11.5,
                      fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
                    ),
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

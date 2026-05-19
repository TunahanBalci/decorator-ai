import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/sample_furniture.dart';
import 'app_notification_service.dart';

class ProductFavoriteService {
  ProductFavoriteService._();

  static final ProductFavoriteService instance = ProductFavoriteService._();
  static const storageKey = 'favorite_furniture_ids';

  final ValueNotifier<Set<String>> favoriteIds = ValueNotifier<Set<String>>(
    <String>{},
  );

  bool _loaded = false;

  Future<Set<String>> loadFavorites() async {
    final prefs = await SharedPreferences.getInstance();
    final values = (prefs.getStringList(storageKey) ?? const <String>[])
        .toSet();
    favoriteIds.value = values;
    _loaded = true;
    return values;
  }

  Future<bool> isFavorite(String productId) async {
    if (!_loaded) await loadFavorites();
    return favoriteIds.value.contains(productId);
  }

  Future<bool> toggleFavorite(String productId, {String? itemName}) async {
    if (productId.trim().isEmpty) return false;
    if (!_loaded) await loadFavorites();

    final updated = Set<String>.from(favoriteIds.value);
    final wasFavorite = updated.contains(productId);
    if (wasFavorite) {
      updated.remove(productId);
    } else {
      updated.add(productId);
    }
    favoriteIds.value = updated;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(storageKey, updated.toList()..sort());

    final notificationName = itemName ?? _sampleFurnitureName(productId);
    if (notificationName != null && notificationName.trim().isNotEmpty) {
      if (wasFavorite) {
        await AppNotificationService.instance.addFavoriteRemoved(
          notificationName,
        );
      } else {
        await AppNotificationService.instance.addFavoriteAdded(
          notificationName,
        );
      }
    }
    return !wasFavorite;
  }

  String? _sampleFurnitureName(String productId) {
    for (final item in sampleFurniture) {
      if (item.id == productId) return item.title;
    }
    return null;
  }
}

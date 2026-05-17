import 'package:flutter/material.dart';

import 'app_colors.dart';

class AppTheme {
  static ThemeData light = ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: AppColors.background,
    fontFamily: 'Arial',
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.violet,
      brightness: Brightness.light,
      surface: AppColors.surface,
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(
        color: AppColors.ink,
        fontSize: 34,
        height: 1.08,
        fontWeight: FontWeight.w800,
      ),
      headlineMedium: TextStyle(
        color: AppColors.ink,
        fontSize: 24,
        fontWeight: FontWeight.w800,
      ),
      titleLarge: TextStyle(
        color: AppColors.ink,
        fontSize: 20,
        fontWeight: FontWeight.w700,
      ),
      bodyLarge: TextStyle(color: AppColors.ink, fontSize: 16, height: 1.45),
      bodyMedium: TextStyle(color: AppColors.muted, fontSize: 14, height: 1.4),
    ),
  );
}

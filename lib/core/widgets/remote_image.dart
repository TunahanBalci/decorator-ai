import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class RemoteImage extends StatelessWidget {
  const RemoteImage({
    required this.url,
    this.fit = BoxFit.cover,
    this.width,
    this.height,
    super.key,
  });

  final String url;
  final BoxFit fit;
  final double? width;
  final double? height;

  @override
  Widget build(BuildContext context) {
    return Image.network(
      url,
      fit: fit,
      width: width,
      height: height,
      errorBuilder: (context, error, stackTrace) {
        return Container(
          color: AppColors.sand,
          alignment: Alignment.center,
          child: const Icon(
            Icons.image_not_supported_outlined,
            color: AppColors.ink,
            size: 42,
          ),
        );
      },
    );
  }
}

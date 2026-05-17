import 'package:flutter/material.dart';

class StoreOffer {
  const StoreOffer({
    required this.storeName,
    required this.price,
    required this.url,
    required this.buttonColor,
  });

  final String storeName;
  final String price;
  final String url;
  final Color buttonColor;
}

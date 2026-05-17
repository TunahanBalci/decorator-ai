import 'product_spot.dart';

class DesignProject {
  const DesignProject({
    required this.id,
    required this.title,
    required this.spaceType,
    required this.style,
    required this.imageUrl,
    required this.products,
  });

  final String id;
  final String title;
  final String spaceType;
  final String style;
  final String imageUrl;
  final List<ProductSpot> products;

  factory DesignProject.fromMap(
    String id,
    Map<String, dynamic> data, {
    List<ProductSpot> products = const <ProductSpot>[],
  }) {
    return DesignProject(
      id: id,
      title: data['title'] as String? ?? '',
      spaceType: data['spaceType'] as String? ?? '',
      style: data['style'] as String? ?? '',
      imageUrl: data['imageUrl'] as String? ?? '',
      products: products,
    );
  }

  Map<String, dynamic> toMap({int? sortOrder, bool isPublished = true}) {
    return {
      'title': title,
      'spaceType': spaceType,
      'style': style,
      'imageUrl': imageUrl,
      'isPublished': isPublished,
      'sortOrder': ?sortOrder,
    };
  }
}

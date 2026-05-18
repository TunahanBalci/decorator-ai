from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from furniture_crawler.items import FurnitureItem
from furniture_crawler.extractors.jsonld_extractor import extract_jsonld, get_product_from_jsonld
from furniture_crawler.extractors.image_extractor import extract_image_urls

class IstikbalSpider(CrawlSpider):
    name = "istikbal"
    custom_settings = {
        'FEEDS': {'istikbal_urunleri.json': {'format': 'json', 'overwrite': True}}
    }
    allowed_domains = ["istikbal.com.tr"]
    
    # İstikbal ana mobilya kategorileri
    start_urls = [
        #"https://www.istikbal.com.tr/"
        "https://www.istikbal.com.tr/kategori/yatak-odasi-takimlari",
        "https://www.istikbal.com.tr/kategori/mutfak-masa-takimi",
    ]
   
    TARGET_CATEGORIES = [
        'baza', 'gardırop', 'komodin', 'yatak başlığı', 'yatak odası takımı', 
        'mutfak masa', 'mutfak sandalyesi', 'dolap', 'makyaj masası','karyola başlğı','makyaj aynası'
        'mutfak masa takımı', 
    ]
    
    rules = (
        # İstikbal'de sayfalama genellikle ?p=1 veya /page/ şeklindedir.
        # Sepet, üye girişi gibi gereksiz sayfaları taramayı reddet (deny)
        Rule(LinkExtractor(
            deny=(r'/customer/', r'/checkout/', r'/cart/', r'/iletisim'),
            unique=True
        ), callback='parse_item', follow=True),
    )
     
    def parse_item(self, response):
        # İstikbal için ürün sayfası doğrulama (Genelde Magento altyapısı class'ları)
        jsonld_data = extract_jsonld(response)
        product_data = get_product_from_jsonld(jsonld_data)

        # 2. ÜRÜN SAYFASI DOĞRULAMA (Eski is_product_page yerine bu blok geldi)
        has_price = bool(response.css('.product-price-new, .product-price, .price-box, [itemprop="price"]'))
        if not (product_data or has_price):
            return

        jsonld_data = extract_jsonld(response)
        detected_categories = []
        
        # 1. Aşama: Breadcrumb Kategorilerini Çıkar (JSON-LD)
        for block in jsonld_data:
            if isinstance(block, dict) and block.get('@type') == 'BreadcrumbList':
                items = block.get('itemListElement', [])
                for element in items:
                    cat_name = None
                    if isinstance(element, dict):
                        item_data = element.get('item')
                        if isinstance(item_data, dict):
                            cat_name = item_data.get('name')
                        if not cat_name:
                            cat_name = element.get('name')
                    elif isinstance(element, str):
                        cat_name = element

                    if cat_name and isinstance(cat_name, str):
                        detected_categories.append(cat_name.strip())
                break 

        # İstikbal CSS Fallback: Breadcrumb
        if not detected_categories:
            css_breadcrumbs = response.css('.breadcrumbs li a::text, .breadcrumbs li strong::text, .breadcrumbs li span::text, .breadcrumb li a::text, .breadcrumb li span::text').getall()
            
            # Ayraçları (>, /) temizle ve listeyi oluştur
            detected_categories = []
            for cat in css_breadcrumbs:
                clean_cat = cat.strip()
                # Boş değilse ve sadece bir ayraç karakterinden ibaret değilse listeye ekle
                if clean_cat and clean_cat not in ['>', '/', '-', '|']:
                    detected_categories.append(clean_cat)

        # 2. Aşama: Beyaz Liste Kontrolü
        is_target_product = False
        for category in detected_categories:
            # Hedef kelimelerimizin (ör: "yatak", "koltuk") sitedeki kategorinin içinde geçip geçmediğine bakıyoruz
            if any(target in category.lower() for target in self.TARGET_CATEGORIES):
                is_target_product = True
                break

        # Hedef ürün değilse işlemi iptal et
        if not is_target_product and detected_categories:
            self.logger.debug(f"Hedef dışı ürün atlandı: {detected_categories}")
            return

        # 3. Aşama: Ürün Verisini Çıkar (JSON-LD)
        product_data = get_product_from_jsonld(jsonld_data)
            
        # 4. Aşama: Item Oluşturma
        item = FurnitureItem()
        item['url'] = response.url
        item['breadcrumbs'] = detected_categories
        
        if product_data:
            item['name'] = product_data.get('name')
            item['description'] = product_data.get('description', '')
            
            offers = product_data.get('offers', {})
            if isinstance(offers, list) and len(offers) > 0:
                offers = offers[0]
                
            item['price'] = offers.get('price')
            item['currency'] = offers.get('priceCurrency')
            item['id'] = product_data.get('sku') or product_data.get('productID')
            item['metadata'] = product_data
        else:
            # İSTİKBAL İÇİN CSS FALLBACK (Magento Standartları)
            item['name'] = response.css('h1.page-title span::text, h1::text').get('').strip()
            item['price'] = response.css('.price-wrapper .price::text, .special-price .price::text').re_first(r'[\d.,]+')
            item['currency'] = "TRY" 
            item['id'] = response.css('.sku .value::text, [itemprop="sku"]::text').get('').strip()
            
            description_texts = response.css('.product.attribute.description .value *::text, #description *::text').getall()
            item['description'] = " ".join([d.strip() for d in description_texts if d.strip()])
            item['metadata'] = {}
            
        # Resim Çıkarma
        item['image_urls'] = extract_image_urls(response, product_data)
        
        if not item.get('id'):
            item['id'] = response.url.split('/')[-1].replace('.html', '')
            
        yield item
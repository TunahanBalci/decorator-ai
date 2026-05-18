from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from furniture_crawler.items import FurnitureItem
from furniture_crawler.extractors.jsonld_extractor import extract_jsonld, get_product_from_jsonld
from furniture_crawler.extractors.image_extractor import extract_image_urls

class IkeaSpider(CrawlSpider):
    name = "ikea"
    allowed_domains = ["ikea.com.tr"]
    
    # 1. DÜZELTME: Vivense kalıntısı silindi, sadece IKEA kategorileri bırakıldı.
    start_urls = [
        "https://www.ikea.com.tr/kategori/mobilyalar",
        "https://www.ikea.com.tr/kategori/yatak-odasi-mobilyalari",
        "https://www.ikea.com.tr/kategori/yemek-odasi-mobilyalari",
    ]
   
    TARGET_CATEGORIES = [
        'çift kişilik baza', 'gardırop', 'komodin', 'yatak başlığı', 'yatak', 
        'karyola', 'mutfak masası', 'mutfak masası takımı', 'mutfak sandalyesi','sandalye',
        'mutfak sandalyeleri', 'çok amaçlı mutfak dolabı', 
        'hazır mutfak dolabı', 'koltuk', 'sehpa', 'masa'
    ]
    
    # 2. DÜZELTME: URL rotalama işlemi izole edildi.
    rules = (
        # Kategori sayfalarında sadece gezin (parse etme, sonraki sayfalara git)
        Rule(LinkExtractor(allow=(r'/kategori/')), follow=True),
        # Sadece Ürün sayfalarında parse_item fonksiyonunu tetikle
        Rule(LinkExtractor(allow=(r'/urun/')), callback='parse_item', follow=True),
    )
     
    def parse_item(self, response):
        # 1. JSON-LD ve Ürün Verisini Çıkar (En başa aldık ki kontrol için kullanabilelim)
        jsonld_data = extract_jsonld(response)
        product_data = get_product_from_jsonld(jsonld_data)

        # 2. ÜRÜN SAYFASI DOĞRULAMA (İstikbal Mantığı: Buton yerine Fiyat/Veri kontrolü)
        has_form = bool(response.css('form#aspnetForm'))
        has_price = bool(response.css('.pip-temp-price, .pip-temp-price__integer, [itemprop="price"]'))
        if not (product_data or has_price):
            return # Fiyat veya ürün datası yoksa ürün sayfası değildir, çık.

        # 3. KATEGORİ (BREADCRUMB) ÇIKARMA
        detected_categories = []
        
        # JSON-LD'den kategori çıkarma
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

        # CSS Fallback: Kategori (Ayraç temizleme eklendi)
        if not detected_categories:
            css_breadcrumbs = response.css('.bc-breadcrumb__item span::text, .bc-breadcrumb__item a::text').getall()
            for cat in css_breadcrumbs:
                clean_cat = cat.strip()
                if clean_cat and clean_cat not in ['>', '/', '-', '|']:
                    detected_categories.append(clean_cat)

        # LOG EKLENDİ: Hangi kategorileri bulup hangilerini sildiğini terminalde görmek için
        if detected_categories:
            self.logger.info(f"BULUNAN KATEGORİLER: {detected_categories} | URL: {response.url}")

        # 4. BEYAZ LİSTE (WHITELIST) KONTROLÜ
        is_target_product = False
        for category in detected_categories:
            if any(target in category.lower() for target in self.TARGET_CATEGORIES):
                is_target_product = True
                break

        if not is_target_product and detected_categories:
            self.logger.debug(f"Hedef dışı ürün atlandı: {detected_categories}")
            return

        # 5. ITEM OLUŞTURMA
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
            # IKEA için Fallback (JSON-LD yoksa)
            item['name'] = response.css('h1::text, .pip-header-section__title--big::text').get('').strip()
            item['price'] = response.css('.pip-temp-price__integer::text').re_first(r'[\d.,]+')
            item['currency'] = "TRY" 
            item['id'] = response.css('.pip-product-identifier__value::text').get('').strip()
            
            description_texts = response.css('.pip-product-summary__description::text, .pip-product-details__paragraph::text').getall()
            item['description'] = " ".join([d.strip() for d in description_texts if d.strip()])
            item['metadata'] = {}
            
        if not item.get('id'):
            item['id'] = response.url.split('/')[-1].replace('.html', '')
            
        # Extract Images
        item['image_urls'] = extract_image_urls(response, product_data)
        
        yield item
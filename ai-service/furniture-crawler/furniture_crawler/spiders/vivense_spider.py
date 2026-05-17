from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from furniture_crawler.items import FurnitureItem
from furniture_crawler.extractors.jsonld_extractor import extract_jsonld, get_product_from_jsonld
from furniture_crawler.extractors.image_extractor import extract_image_urls

class VivenseSpider(CrawlSpider):
    name = "vivense"
    allowed_domains = ["vivense.com"]
    start_urls = ["https://www.vivense.com/sitemap.html"]
   

    # Elenmesini istediğin ana kategori başlıkları
    TARGET_CATEGORIES = [
            'yatak odası takımı', 'baza', 'gardırop', 'komodin', 'yatak başlığı', 'yatak', 
            'karyola', 'gardırop', 'mutfak masası', 'mutfak-masa-takımı', 'Mutfak Masası',
            'Mutfak sandalyeleri', 'Çok amaçlı mutfak dolabı', 'Hazır mutfak dolabı'
    ]
    
    rules = (
        #Follow all links to discover products
        Rule(LinkExtractor(allow=()), callback='parse_item', follow=True),
    )
     
    def parse_item(self, response):
        # Extract JSON-LD data
        jsonld_data = extract_jsonld(response)

        # 1. Aşama: JSON-LD içinden BreadcrumbList'i bul ve kategorileri çıkar
        detected_categories = []
        for block in jsonld_data:
            if isinstance(block, dict) and block.get('@type') == 'BreadcrumbList':
                items = block.get('itemListElement', [])
                for element in items:
                    cat_name = None
                    
                    # 1. Eğer veri beklediğimiz gibi bir sözlük (dict) ise:
                    if isinstance(element, dict):
                        item_data = element.get('item')
                        if isinstance(item_data, dict):
                            cat_name = item_data.get('name')
                        if not cat_name:
                            cat_name = element.get('name')
                            
                    # 2. Eğer Vivense oraya dümdüz bir metin (string) koyduysa:
                    elif isinstance(element, str):
                        cat_name = element

                    # Eğer geçerli bir isim bulduysak listeye ekle
                    if cat_name and isinstance(cat_name, str):
                        detected_categories.append(cat_name.strip())

        # YENİ KONTROL (Beyaz Liste Mantığı): 
        # Breadcrumb içinde bizim HEDEF kelimelerimizden biri var mı?
        is_target_product = False
        for category in detected_categories:
            if any(target in category.lower() for target in self.TARGET_CATEGORIES):
                is_target_product = True
                break

        # Eğer hiçbir hedef kelimeyle eşleşmediyse (Örn: Çay bardağı, Halı, Matkap geldi)
        if not is_target_product:
            self.logger.debug(f"Hedef dışı ürün atlandı: {detected_categories}")
            return # Çöpe at!

        # 2. Aşama: Product bilgisini çıkar (Artık bu ürün kesin hedeflerimizden biri!)
        product_data = get_product_from_jsonld(jsonld_data)

        is_product_page = bool(product_data) or bool(response.css('.add-to-cart-button, #add-to-cart'))
        if not is_product_page:
            return

        # Ürün oluşturma ve verileri aktarma
        item = FurnitureItem()
        item['url'] = response.url
        
        # ... Diğer ürün verilerini (isim, fiyat vs.) çekme işlemleri ...
        
        # Topladığımız breadcrumb listesini de item'a aktarıyoruz
        item['breadcrumbs'] = detected_categories
        
#################

        product_data = get_product_from_jsonld(jsonld_data)
        
        # Fallback to check if it's a product page even without JSON-LD
        # For example, look for add to cart button
        is_product_page = bool(product_data) or bool(response.css('.add-to-cart-button, #add-to-cart'))
        
        if not is_product_page:
            self.logger.debug(f"Not a product page: {response.url}")
            return
            
        item = FurnitureItem()
        item['url'] = response.url
        
        if product_data:
            item['name'] = product_data.get('name')
            item['description'] = product_data.get('description', '')
            
            # Price extraction
            offers = product_data.get('offers', {})
            if isinstance(offers, list) and len(offers) > 0:
                offers = offers[0]
                
            item['price'] = offers.get('price')
            item['currency'] = offers.get('priceCurrency')
            
            # Product ID (SKU)
            item['id'] = product_data.get('sku') or product_data.get('productID')
            
            # Metadata
            item['metadata'] = product_data
        else:
            # Fallback extraction from HTML if JSON-LD is missing but it is a product page
            item['name'] = response.css('h1::text').get('').strip()
            item['price'] = response.css('.price::text, .product-price::text').re_first(r'[\d.,]+')
            item['currency'] = "TRY" # Assuming Turkish store as fallback
            item['id'] = response.url.split('/')[-1].split('.')[0]
            item['description'] = response.css('.product-description *::text').getall()
            item['metadata'] = {}
            
        # Ensure we have a product ID
        if not item.get('id'):
            item['id'] = response.url.split('/')[-1].replace('.html', '')
            
        # Extract Images
        image_urls = extract_image_urls(response, product_data)
        item['image_urls'] = image_urls
        
        yield item

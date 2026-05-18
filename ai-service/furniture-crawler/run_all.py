from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Spider sınıflarımızı içeri aktarıyoruz
from furniture_crawler.spiders.ikea_spider import IkeaSpider
from furniture_crawler.spiders.vivense_spider import VivenseSpider
from furniture_crawler.spiders.istikbal_spider import IstikbalSpider

def main():
    print("Veri kazıma süreci başlatılıyor...")
    
    # settings.py dosyasındaki hayati ayarları (User-Agent, Delay vb.) yükle
    settings = get_project_settings()
    
    # Süreci başlatacak motoru oluştur
    process = CrawlerProcess(settings)
    
    # Botları motora ekle
    process.crawl(IkeaSpider)
    process.crawl(VivenseSpider)
    process.crawl(IstikbalSpider)
    
    # Motoru ateşle (Bu satır çalışınca 3 site de aynı anda asenkron taranmaya başlar)
    process.start()
    
    print("Tüm veri kazıma işlemleri tamamlandı!")

if __name__ == "__main__":
    main()
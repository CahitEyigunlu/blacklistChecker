# blacklistChecker

Bu proje, belirli bir IP adresinin veya IP adresi listesinin çeşitli kara listelerde (blacklist) olup olmadığını kontrol etmek için bir Python betiğidir. 

## Özellikler

* Çoklu kara liste desteği (Spamhaus, Barracuda, SORBS, vb.)
* Tek bir IP adresi veya bir IP adresi listesi kontrol etme yeteneği
* Kara listeye alınmış IP adresleri için ek bilgi sağlama (kaldırma bağlantısı, kaldırma yöntemi)
* YAML tabanlı yapılandırma dosyası ile kolay özelleştirme

## Gereksinimler

* Python 3.6 veya üstü
* `PyYAML` kütüphanesi

## Kurulum

1. Projeyi klonlayın veya indirin.
2. Gerekli kütüphaneleri yükleyin: `pip install -r requirements.txt`

## Kullanım :
python blacklist_checker.py [IP adresi veya dosya yolu]
* **IP adresi:** Tek bir IP adresini kontrol etmek için doğrudan IP adresini girin.
* **Dosya yolu:** Birden fazla IP adresini kontrol etmek için IP adreslerini içeren bir dosyanın yolunu girin (her satırda bir IP adresi).

## Yapılandırma

`config.yml` dosyasını düzenleyerek kara listeleri ve diğer ayarları özelleştirebilirsiniz.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.


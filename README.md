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

## Kullanım
import time

import dns.resolver

from utils.config_manager import load_config
from utils.display import Display
from logger import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")


class BlacklistTests:
    def __init__(self):
        pass

    def run(self):
        """
        Kara liste sağlık kontrol testini çalıştırır ve sonucu döndürür.
        """
        return self.test_blacklist_health()

    def test_blacklist_health(self, test_ip="127.0.0.2"):
        """
        Karaliste DNS sağlık kontrolü yapar ve sonucu döndürür.
        Her bir karalisteye test_ip üzerinden DNS sorgusu yapar.
        Yanıt alınan durumlarda süreyi kaydeder, alınamayanlarda durumu açıklayıcı bir şekilde rapor eder.
        :param test_ip: Test edilecek IP adresi (varsayılan: 127.0.0.2)
        """
        try:
            # Config dosyasını yükle
            config = load_config()

            if not config or 'blacklists' not in config:
                raise ValueError("Karaliste bilgileri 'blacklists' altında bulunamadı.")

            # Karaliste sonuçlarını tutmak için bir sözlük
            blacklist_results = {}

            # Her bir karaliste için DNS sorgusu yap
            for blacklist in config['blacklists']:
                name = blacklist.get('name', 'Unknown')
                dns_address = blacklist.get('dns', None)

                if not dns_address:
                    error_logger.error(f"Karaliste DNS bilgisi eksik: {name}")
                    Display.print_warning(f"DNS bilgisi eksik: {name}")
                    blacklist_results[name] = {
                        "status": "Eksik DNS bilgisi",
                        "response_time": 0
                    }
                    continue

                try:
                    Display.print_info(f"{name} ({dns_address}) kontrol ediliyor...")

                    # Zaman ölçümü başlat
                    start_time = time.time()

                    # DNS sorgusu (test_ip üzerine)
                    query = f"{test_ip}.{dns_address}"
                    answers = dns.resolver.resolve(query, "A")  # "A" kaydı sorgulanır

                    # Zaman ölçümü durdur
                    elapsed_time = round((time.time() - start_time) * 1000, 2)  # Milisaniye cinsinden
                    blacklist_results[name] = {
                        "status": "IP kara listede",
                        "response_time": elapsed_time,
                        "answers": [answer.to_text() for answer in answers]
                    }

                    # Başarı mesajı
                    info_logger.info(f"{name} ({dns_address}) IP kara listede. Yanıt süresi: {elapsed_time} ms")
                    Display.print_success(f"{name} ({dns_address}) IP kara listede. Yanıt süresi: {elapsed_time} ms")

                except dns.resolver.NXDOMAIN:
                    # Kara listede olmadığını belirtir
                    blacklist_results[name] = {
                        "status": "IP kara listede değil",
                        "response_time": 0
                    }
                    Display.print_info(f"{name} ({dns_address}): IP kara listede değil.")
                    info_logger.info(f"{name} ({dns_address}): IP kara listede değil.")

                except dns.resolver.Timeout:
                    # DNS sorgusu zaman aşımına uğradı
                    blacklist_results[name] = {
                        "status": "DNS sorgusu zaman aşımına uğradı",
                        "response_time": 0
                    }
                    Display.print_warning(f"{name} ({dns_address}): DNS sorgusu zaman aşımına uğradı.")
                    error_logger.error(f"{name} ({dns_address}): DNS sorgusu zaman aşımına uğradı.")

                except dns.resolver.NoAnswer:
                    # DNS sorgusu yanıt vermedi
                    blacklist_results[name] = {
                        "status": "DNS yanıt vermedi",
                        "response_time": 0
                    }
                    Display.print_warning(f"{name} ({dns_address}): DNS yanıt vermedi.")
                    error_logger.error(f"{name} ({dns_address}): DNS yanıt vermedi.")

                except Exception as e:
                    # Diğer tüm hatalar
                    blacklist_results[name] = {
                        "status": "Beklenmeyen hata",
                        "response_time": 0,
                        "error": str(e)
                    }
                    Display.print_error(f"{name} ({dns_address}) beklenmeyen bir hata nedeniyle çalışmıyor. Hata: {str(e)}")
                    error_logger.error(f"{name} ({dns_address}): Beklenmeyen hata. {str(e)}")

            # Tüm sonuçları kullanıcıya göster
            Display.print_info("Karaliste Sağlık Kontrol Sonuçları:")
            for name, result in blacklist_results.items():
                if result["response_time"] > 0:
                    Display.print_info(f"{name}: {result['status']} - {result['response_time']} ms")
                else:
                    Display.print_warning(f"{name}: {result['status']} (Hata: {result.get('error', 'Belirtilmedi')})")

            return all(result["status"] in ("IP kara listede", "IP kara listede değil") for result in blacklist_results.values())

        except Exception as e:
            # Genel hata loglama ve kullanıcıya gösterim
            error_logger.error(f"Karaliste sağlık kontrolü başarısız: {str(e)}")
            Display.print_error("Karaliste sağlık kontrolü başarısız.")
            return False
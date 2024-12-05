import dns.resolver

class QueryCommand:
    """
    DNS sorguları ile kara liste kontrolü yapmak için bir sınıf.
    """

    def __init__(self, blacklist_dns):
        """
        Sınıfı başlatır.

        Args:
          blacklist_dns: Kara liste DNS adresi.
        """
        self.blacklist_dns = blacklist_dns

    def check_blacklist(self, ip_address):
        """
        Bir IP adresinin kara listede olup olmadığını kontrol eder.

        Args:
          ip_address: Kontrol edilecek IP adresi.

        Returns:
          bool: IP adresi kara listede ise True, değilse False.
        """
        try:
            # DNS sorgusu oluştur
            query = f"{ip_address}.{self.blacklist_dns}"

            # DNS sorgusu yap
            answers = dns.resolver.resolve(query, "A")

            # Eğer yanıt alınırsa IP kara listededir
            return True
        except dns.resolver.NXDOMAIN:
            # Yanıt alınamazsa IP kara listede değildir
            return False
        except dns.resolver.NoAnswer:
            # DNS sunucusu yanıt vermezse hata döndür
            raise Exception("DNS sunucusu yanıt vermedi.")
        except dns.resolver.Timeout:
            # DNS sorgusu zaman aşımına uğrarsa hata döndür
            raise Exception("DNS sorgusu zaman aşımına uğradı.")
        except Exception as e:
            # Diğer hatalar için hata döndür
            raise Exception(f"DNS sorgusu sırasında hata oluştu: {e}")
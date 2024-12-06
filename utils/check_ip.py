import dns.resolver

def check_ip_blacklist(ip, dns_suffix):
    """
    Checks if an IP address is listed in a specified blacklist.

    Args:
        ip (str): The IP address to check.
        dns_suffix (str): The DNS suffix of the blacklist (e.g., "zen.spamhaus.org").

    Returns:
        bool: True if the IP is blacklisted, False otherwise.
    """
    try:
        # IP adresini ters çevirerek DNS formatına uygun hale getir
        reversed_ip = ".".join(reversed(ip.split(".")))
        query = f"{reversed_ip}.{dns_suffix}"
        
        # DNS sorgusu yap
        dns.resolver.resolve(query, "A")
        # Eğer sorgu başarılıysa IP kara listededir
        return True
    except dns.resolver.NXDOMAIN:
        # NXDOMAIN, IP'nin kara listede olmadığını gösterir
        return False
    except dns.resolver.Timeout:
        # Zaman aşımı durumunda hata mesajı döndür
        raise Exception("DNS query timed out.")
    except Exception as e:
        # Diğer hatalar için mesaj
        raise Exception(f"Error occurred during DNS query: {e}")

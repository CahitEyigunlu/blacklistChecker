#!/bin/bash

# Zaman damgası oluştur
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
backup_dir="backup"
backup_file="$backup_dir/backup_$timestamp.zip"

# Backup klasörü oluştur (eğer yoksa)
if [ ! -d "$backup_dir" ]; then
    mkdir -p "$backup_dir"
    echo "Backup klasörü oluşturuldu: $backup_dir"
fi

# .git ve logs klasörlerini hariç tutarak sıkıştırma
echo "Sıkıştırma işlemi başlıyor..."
zip -r "$backup_file" . -x ".git/*" "logs/*" "*.zip"

# Eğer sıkıştırma başarısız olursa hata mesajı göster
if [ $? -ne 0 ]; then
    echo "Sıkıştırma işlemi başarısız oldu!"
else
    echo "Yedekleme tamamlandı: $backup_file"
fi

#!/bin/bash

# Zaman damgası oluştur
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
backup_dir="backup"
backup_file="backup_$timestamp.zip"

# .git ve logs klasörlerini hariç tutarak sıkıştırma
echo "Sıkıştırma işlemi başlıyor..."
zip -r "$backup_file" . -x ".git/*" "logs/*" "*.zip"

# Eğer sıkıştırma başarısız olursa backup klasörü oluştur ve oraya kaydet
if [ $? -ne 0 ]; then
    echo "Sıkıştırma başarısız oldu, yedekleme dizini oluşturuluyor..."
    mkdir -p "$backup_dir"
    mv "$backup_file" "$backup_dir/"
    echo "Yedekleme tamamlandı: $backup_dir/$backup_file"
else
    echo "Sıkıştırma tamamlandı: $backup_file"
fi

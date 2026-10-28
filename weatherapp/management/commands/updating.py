import json
from django.core.management.base import BaseCommand
from weatherapp.services import get_weather_by_city
from weatherapp.models import CityWeather


class Command(BaseCommand): # basecommand ile dosyamızı bir terminal komutu ile çalışan bir şey olarak tanır
    help = '81 ilin hava durumunu JSON dosyasından okur ve veritabanını günceller'
    # python manage.py guncelle_hava --help yazınca çıkacak olan mesajdır

    def handle(self, *args, **options):
        # 1. JSON dosyasını oku (Extract)
        with open('weatherapp/cities.json', 'r', encoding='utf-8') as f:
            cities = json.load(f)

        self.stdout.write(self.style.SUCCESS(f"{len(cities)} şehir işleniyor..."))

        for city in cities:
            city_name = city['name']
            self.stdout.write(f"{city_name} için veriler çekiliyor...")

            # 2. Senin yazdığın o gelişmiş servisi çağır (Transform)
            # Bu fonksiyon zaten AI yorumunu yapıyor, Spotify linkini alıyor ve gelecek saatleri liste yapıyor.
            weather_data_list = get_weather_by_city(city_name)

            if weather_data_list:
                data = weather_data_list[0]
                
                # 3. Veritabanına kaydet (Load)
                CityWeather.objects.update_or_create(
                    city_name=data['city'],
                    defaults={
                        'temperature': data['temperature'],
                        'humidity': data['humidity'],
                        'comfort_score': data['comfort_score'],
                        'next_temps': data['next_temps'], # JSON listesi buraya gidiyor
                        # Modeline ai_comment ve spotify_url alanlarını eklemeyi unutma!
                    }
                )
                self.stdout.write(self.style.SUCCESS(f"✔ {city_name} güncellendi."))
            
        self.stdout.write(self.style.SUCCESS("Tüm şehirler başarıyla güncellendi!"))
from django.shortcuts import render
from django.utils import timezone
from .services import (
    fetch_om_data, 
    fetch_ow_current, 
    save_merged_data, 
    get_ai_comment, 
    hesapla_konfor
)
from .sposervices import get_playlist
from .models import MergedForecast

CITY_COORDINATES = {
    "Ankara": (39.93, 32.85),
    "İstanbul": (41.00, 28.97),
    "İzmir": (38.41, 27.12),
}

# Emoji Seçici Fonksiyon (Şimdilik sadece sıcaklığa bakarak tahmin yürütüyor)
def get_weather_emoji(condition):
    if not condition:
        return "🌡️"
    condition = condition.lower()
    if "rain" in condition or "yağmur" in condition: return "🌧️"
    if "snow" in condition or "kar" in condition: return "❄️"
    if "cloud" in condition or "bulut" in condition: return "☁️"
    if "clear" in condition or "açık" in condition: return "☀️"
    if "storm" in condition or "fırtına" in condition: return "⛈️"
    return "🌡️"

def home_page(request):
    aranan_sehir = request.GET.get('city', 'Ankara')
    
    if aranan_sehir in CITY_COORDINATES:
        lat, lon = CITY_COORDINATES[aranan_sehir]
        fetch_om_data(aranan_sehir, lat, lon)
        fetch_ow_current(aranan_sehir, lat, lon)
        save_merged_data(aranan_sehir)

    simdi = timezone.now()
    
    anlik_veri = MergedForecast.objects.filter(
        city_name__iexact=aranan_sehir,
        forecast_time__gte=simdi
    ).order_by('forecast_time').first()

    if not anlik_veri:
        anlik_veri = MergedForecast.objects.filter(city_name__iexact=aranan_sehir).first()

    gelecek_saatler = MergedForecast.objects.filter(
        city_name__iexact=aranan_sehir,
        forecast_time__gt=simdi
    ).order_by('forecast_time')[:5]

    ai_yorumu = ""
    konfor_puani = 0
    spotify_sarki = None
    ruzgar = 0
    hava_emoji = "🌡️" # Varsayılan emoji
    
    if anlik_veri:
        temp = anlik_veri.temperature or 0
        hum = anlik_veri.humidity or 0
        precip = anlik_veri.precipitation_chance or 0
        ruzgar = anlik_veri.wind_speed or 0
        
        # Condition verisi modelde varsa onu kullan, yoksa sıcaklığa göre tahmin et
        condition = getattr(anlik_veri, 'condition', None)
        if not condition:
            # Eğer condition verisi yoksa, sıcaklığa göre bir tahmin yürütelim
            if precip > 50: condition = "Rain"
            elif temp < 0: condition = "Snow"
            elif temp > 25: condition = "Clear"
            else: condition = "Clouds"
            
        hava_emoji = get_weather_emoji(condition)
        
        ai_yorumu = get_ai_comment(temp, hum, precip)
        konfor_puani = hesapla_konfor(temp, hum, ruzgar, precip)
        spotify_sarki = get_playlist(temp)

    context = {
        'hava': anlik_veri,
        'gelecek_saatler': gelecek_saatler,
        'aranan_sehir': aranan_sehir,
        'ai_yorumu': ai_yorumu,
        'konfor_puani': konfor_puani,
        'ruzgar': ruzgar,
        'sarki': spotify_sarki,
        'hava_emoji': hava_emoji, # <--- EMOJİYİ HTML'E GÖNDERİYORUZ
    }
    
    return render(request, 'weatherapp/homepage.html', context)
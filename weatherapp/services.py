
import os
import requests
import pandas as pd
from google import genai
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from .models import HourlyForecast, MergedForecast
from google.genai.errors import APIError

def hesapla_konfor(sicaklik, nem, ruzgar):
    puan = 100
    if sicaklik < 10:
        puan -= (10 - sicaklik) * 3
    elif sicaklik > 28:
        puan -= (sicaklik - 28) * 3
    if nem < 30:
        puan -= (30 - nem) * 0.5
    elif nem > 60:
        puan -= (nem - 60) * 0.5
    if ruzgar > 15:
        puan -= (ruzgar - 15) * 1
    return max(0, min(100, int(puan)))

def fetch_om_data(city_name, lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m",
        "timezone": "UTC",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print("Open-Meteo hatasi:", e)
        return 0

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    precips = hourly.get("precipitation_probability", [])

    now = timezone.now()
    saved_count = 0

    for t_str, temp, hum, precip in zip(
        times, temps, humidities, precips
    ):
        if temp is None:
            continue

        forecast_dt = datetime.fromisoformat(t_str)

        # API saatleri UTC olarak isteniyor.
        if forecast_dt.tzinfo is None:
            forecast_dt = forecast_dt.replace(tzinfo=dt_timezone.utc)
        else:
            forecast_dt = forecast_dt.astimezone(dt_timezone.utc)

        if forecast_dt < now:
            continue

        defaults = {
            "temperature": temp,
            "humidity": hum,
            "precipitation_chance": precip,
        }

        _, created = HourlyForecast.objects.update_or_create(
            city_name=city_name,
            source="openmeteo",
            forecast_time=forecast_dt,
            defaults=defaults,
        )

        if created:
            saved_count += 1

    print(f"[{city_name}] Open-Meteo: {saved_count} yeni kayıt.")
    return saved_count


def fetch_ow_current(city_name, lat, lon):
    api_key = os.getenv("OPEN_WEATHER_KEY")

    if not api_key:
        print("OPEN_WEATHER_KEY bulunamadi!")
        return 0

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print("OpenWeather hatasi:", e)
        return 0

    forecast_list = data.get("list", [])
    now = timezone.now()
    saved_count = 0

    for item in forecast_list:
        if "dt" not in item or "main" not in item:
            continue

        forecast_dt = datetime.fromtimestamp(
            item["dt"],
            tz=dt_timezone.utc,
        )

        if forecast_dt < now:
            continue

        main = item["main"]

        defaults = {
            "wind_speed": item["wind"]["speed"],    
            "temperature": main.get("temp"),
            "humidity": main.get("humidity"),
            "precipitation_chance": (
                round(item["pop"] * 100)
                if item.get("pop") is not None
                else None
            ),
        }

        _, created = HourlyForecast.objects.update_or_create(
            city_name=city_name,
            source="openweather",
            forecast_time=forecast_dt,
            defaults=defaults,
        )

        if created:
            saved_count += 1

    print(f"[{city_name}] OpenWeather: {saved_count} yeni kayıt.")
    return saved_count


def data_avg(city_name):
    # Verileri çek
    om_records = list(HourlyForecast.objects.filter(
        city_name__iexact=city_name, source="openmeteo"
    ).values("forecast_time", "temperature", "humidity", "precipitation_chance"))

    ow_records = list(HourlyForecast.objects.filter(
        city_name__iexact=city_name, source="openweather"
    ).values("forecast_time", "temperature", "humidity", "precipitation_chance"))

    if not om_records and not ow_records:
        return []

    columns = ["forecast_time", "temperature", "humidity", "precipitation_chance"]
    om_df = pd.DataFrame(om_records, columns=columns)
    ow_df = pd.DataFrame(ow_records, columns=columns)

    # Tarihleri datetime yap ve index olarak ayarla
    for df in (om_df, ow_df):
        if not df.empty:
            df["forecast_time"] = pd.to_datetime(df["forecast_time"], utc=True)
            df.set_index("forecast_time", inplace=True)
            df.sort_index(inplace=True)

    # İsimleri ayır
    om_df = om_df.rename(columns={
        "temperature": "temperature_om", "humidity": "humidity_om", "precipitation_chance": "precipitation_om"
    })
    ow_df = ow_df.rename(columns={
        "temperature": "temperature_ow", "humidity": "humidity_ow", "precipitation_chance": "precipitation_ow"
    })

    if not om_df.empty and not ow_df.empty:
        merged = pd.merge(om_df, ow_df, left_index=True, right_index=True, how="outer")
        merged = merged.resample('h').interpolate(method='time')
    else:
        merged = pd.merge(om_df, ow_df, left_index=True, right_index=True, how="outer")

    for field in ("temperature", "humidity", "precipitation", "wind_speed"):
        om_col = f"{field}_om"
        ow_col = f"{field}_ow"

        # Sütun yoksa oluştur (biri boş gelirse hata vermesin diye)
        if om_col not in merged: merged[om_col] = None
        if ow_col not in merged: merged[ow_col] = None

        merged[field] = merged[om_col].combine_first(merged[ow_col])
        both = merged[om_col].notna() & merged[ow_col].notna()
        merged.loc[both, field] = (merged.loc[both, om_col] + merged.loc[both, ow_col]) / 2

    # Sıcaklık farkı
    both_temps = merged["temperature_om"].notna() & merged["temperature_ow"].notna()
    merged["temperature_diff"] = (merged["temperature_om"] - merged["temperature_ow"]).abs()
    merged.loc[~both_temps, "temperature_diff"] = float("nan")

    # Kaynak belirleme
    om_exists = merged["temperature_om"].notna()
    ow_exists = merged["temperature_ow"].notna()
    merged["source"] = "none"
    merged.loc[om_exists & ~ow_exists, "source"] = "openmeteo"
    merged.loc[~om_exists & ow_exists, "source"] = "openweather"
    merged.loc[om_exists & ow_exists, "source"] = "avg"

    merged = merged.reset_index().rename(columns={"index": "forecast_time"})
    

    merged = merged.sort_values("forecast_time")
    merged = merged.astype(object).where(pd.notna(merged), None)

    return merged.to_dict(orient="records")

def save_merged_data(city_name):
    birlesik_veri = data_avg(city_name)
    if not birlesik_veri:
        return 0

    saved_count = 0
    for row in birlesik_veri:
        temp = row['temperature'] if row['temperature'] is not None else None
        hum = row['humidity'] if row['humidity'] is not None else None
        precip = row['precipitation'] if row['precipitation'] is not None else None
        # Rüzgar hızını da alıyoruz (data_avg'dan gelecek)
        ruzgar = row.get('wind_speed') if row.get('wind_speed') is not None else None 

        defaults = {
            "temperature": temp,
            "humidity": hum,
            "precipitation_chance": precip,
            "wind_speed": ruzgar, # <--- BURAYA EKLENDİ
            "source_info": row['source']
        }

        obj, created = MergedForecast.objects.update_or_create(
            city_name=city_name,
            forecast_time=row['forecast_time'],
            defaults=defaults
        )
        if created:
            saved_count += 1
            
    print(f"[{city_name}] {saved_count} adet birleştirilmiş veri kaydedildi.")
    return saved_count


def get_ai_comment(temperature, humidity, precipitation):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI yorumu için API anahtarı bulunamadı."
    
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Şu anki hava durumu verileri:
        - Sıcaklık: {temperature}°C
        - Nem: %{humidity}
        - Yağış İhtimali: %{precipitation}
        
        Lütfen bu havaya göre bir insana 2-3 cümlelik samimi, motive edici bir yorum yap. 
        Aynı zamanda bu havada ne giyilmesi gerektiğiyle ilgili (örneğin: "Bugün hafif bir hırka yeterli olur" gibi) çok kısa bir kıyafet önerisi ekle. 
        Yanıtın toplamda 40 kelimeyi geçmesin.
        """
    
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        # Sunucu yoğun veya hata verirse site çökmesin, geçici bir metin dönsün
        return "Şu an hava durumu için yapay zeka yorumu oluşturulamıyor, lütfen biraz sonra tekrar deneyin."


    
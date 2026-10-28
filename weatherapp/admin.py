from django.contrib import admin
from .models import HourlyForecast

@admin.register(HourlyForecast)
class HourlyForecastAdmin(admin.ModelAdmin):
    display = ('city_name', 'temperature', 'humidity', 'precipitation_chance', 'forecast_time')
    search = ('city_name',)
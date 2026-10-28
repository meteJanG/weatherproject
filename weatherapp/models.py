from django.db import models

class HourlyForecast(models.Model):
    city_name = models.CharField(max_length=100)
    source = models.CharField(max_length=50)
    temperature = models.FloatField()
    humidity = models.IntegerField(null=True, blank=True)
    precipitation_chance = models.IntegerField(null=True, blank=True) # yagis ihtimali
    forecast_time = models.DateTimeField()    # verinin alindigi saat
    fetched_at = models.DateTimeField(auto_now_add=True) # verinin cekildigi tarih
    wind_speed = models.FloatField(null=True, blank=True)



class MergedForecast(models.Model):
    city_name = models.CharField(max_length=100)
    forecast_time = models.DateTimeField()
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    precipitation_chance = models.FloatField(null=True, blank=True)
    source_info = models.CharField(max_length=50, default="avg") # 'avg', 'openmeteo' vs.
    wind_speed = models.FloatField(null=True, blank=True)

    
    class Meta:
        unique_together = ('city_name', 'forecast_time')

    def __str__(self):
        return f"{self.city_name} - {self.forecast_time}"
    def __str__(self):
        return f"{self.city_name} - {self.source} - {self.forecast_time.strftime('%Y-%m-%d %H:%M')} ({self.temperature}°C)"
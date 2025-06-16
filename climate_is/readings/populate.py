from stations.models import Station, Sensor, SensorSeries
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

# выдали каждой станции датчики
def add_sensors_to_stations():
    stations = Station.objects.exclude(name__icontains='Пермь')
    perm_sensors = Sensor.objects.filter(station__name__icontains='Пермь')
    sensor_models = {s.sensor_model.param_type.code: s.sensor_model for s in perm_sensors}
    
    for station in stations:
        print(f"Обрабатываем станцию: {station.name}")
        for param_code, model in sensor_models.items():
            # Проверяем, есть ли уже такой датчик
            if not Sensor.objects.filter(station=station, sensor_model=model).exists():
                Sensor.objects.create(
                    station=station,
                    sensor_model=model,
                    last_spoke=timezone.now()
                )
                print(f"Добавлен датчик {param_code} типа {model} станции {station}")

from decimal import Decimal

import random
from datetime import timedelta
from django.utils import timezone
from .models import Reading

def generate_data_based_on_perm():
    # Получаем пермские данные за последние 1 дней
    perm_station = Station.objects.get(name__icontains='Пермь')
    cutoff_date = timezone.now() - timedelta(days=90)
    
    perm_readings = Reading.objects.filter(
        sensor__station=perm_station,
        timestamp__lt=cutoff_date  # Только данные ДО cutoff_date
    ).select_related('sensor')
    
    # Коэффициенты для разных параметров 
    PARAM_COEFFICIENTS = {
        'TEMP': 0.8,   
        'HUM': 1.1,     
        'PRECIP': 0.7,  
        'WS': 0.9,      
        'PRES': 1.0     
    }
    
    # Генерируем данные для других станций
    other_stations = Station.objects.exclude(name__icontains='Пермь')
    
    for station in other_stations:
        print(f"Генерация данных для {station.name}")
        
        # Географический коэффициент 
        lat_diff = station.latitude - perm_station.latitude
        lat_diff_float = float(lat_diff)
        lat_coeff = 1 + lat_diff_float * 0.02  # 2% изменения на градус широты
        
        for perm_reading in perm_readings:
            param_code = perm_reading.sensor.sensor_model.param_type.code
            
            coeff = PARAM_COEFFICIENTS.get(param_code, 1.0)
            
            random_factor = 1 + random.uniform(-0.2, 0.2)
            
            # Итоговое значение с учетом всех поправок
            new_value = perm_reading.value * coeff * lat_coeff * random_factor
            
            # Особые правила для некоторых параметров
            if param_code == 'PRECIP':
                new_value = max(0, new_value)  # Осадки не могут быть отрицательными
            elif param_code == 'HUM':
                new_value = min(100, new_value)  # Влажность не более 100%
            
            # Получаем соответствующий датчик на текущей станции
            try:
                sensor = Sensor.objects.get(
                    station=station,
                    sensor_model__param_type__code=param_code
                )
                
                new_timestamp = perm_reading.timestamp
                
                Reading.objects.create(
                    sensor=sensor,
                    value=round(new_value, 2),
                    timestamp=new_timestamp
                )
                print(f'{param_code}: {perm_reading.value} в {round(new_value, 2)}')
            except Sensor.DoesNotExist:
                print(f"Нет датчика {param_code} на станции {station.name}")
                continue
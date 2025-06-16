import os
import django
from datetime import datetime, timezone
from django.core.exceptions import ObjectDoesNotExist

# скриптик чтобы данные закинуть
# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'climate_is.settings')
django.setup()

from stations.models import Station, ParameterType, Sensor
from readings.models import Reading

def import_meteo_data(file_path):
    # Получаем станцию Пермь
    try:
        perm_station = Station.objects.get(name__icontains='Пермь')
    except ObjectDoesNotExist:
        print("Станция 'Пермь' не найдена в базе данных.")
        return
    
    # Словарь для соответствия параметров и их кодов
    param_mapping = {
        'wind_speed': 'WS',
        'precipitation': 'PRECIP',
        'temperature': 'TEMP',
        'humidity': 'HUM',
        'pressure': 'PRES'
    }
    
    # Словарь для хранения датчиков станции
    sensors_cache = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Пропускаем пустые строки
            if not line.strip():
                continue
                
            try:
                # Разбиваем строку на части
                parts = [p.strip() for p in line.split(';')]
                
                # Парсим дату и время
                year = int(parts[1])
                month = int(parts[2])
                day = int(parts[3])
                hour = int(parts[4])
                
                # Пропускаем записи не в 3:00 и не в 12:00 (кроме осадков)
                if hour not in [3, 12]:
                    continue
                
                # Создаем datetime объект
                timestamp = datetime(year, month, day, hour, tzinfo=timezone.utc)
                
                # Парсим параметры
                wind_speed = float(parts[5]) if parts[5] else None
                precipitation = float(parts[6]) if parts[6] else None
                temperature = float(parts[7]) if parts[7] else None
                humidity = float(parts[8]) if parts[8] else None
                pressure = float(parts[9]) if parts[9] else None
                
            except (IndexError, ValueError) as e:
                print(f"Ошибка в строке {line_num}: {line.strip()}. Ошибка: {str(e)}")
                continue
            
            # Обрабатываем осадки (PRECIP) - сохраняем только ненулевые значения
            if precipitation is not None and precipitation != 0.0:
                try:
                    if 'PRECIP' not in sensors_cache:
                        sensor = Sensor.objects.get(
                            station=perm_station,
                            sensor_model__param_type__code='PRECIP'
                        )
                        sensors_cache['PRECIP'] = sensor
                    else:
                        sensor = sensors_cache['PRECIP']
                    
                    Reading.objects.create(
                        sensor=sensor,
                        value=precipitation,
                        timestamp=timestamp
                    )
                except Exception as e:
                    print(f"Ошибка сохранения осадков (строка {line_num}): {str(e)}")
            
            # Обрабатываем остальные параметры (только для 3:00 и 12:00)
            for param_name, param_code in param_mapping.items():
                if param_code == 'PRECIP':
                    continue  # осадки уже обработаны
                
                value = locals().get(param_name)
                if value is None:
                    continue
                
                try:
                    if param_code not in sensors_cache:
                        sensor = Sensor.objects.get(
                            station=perm_station,
                            sensor_model__param_type__code=param_code
                        )
                        sensors_cache[param_code] = sensor
                    else:
                        sensor = sensors_cache[param_code]
                    
                    Reading.objects.create(
                        sensor=sensor,
                        value=value,
                        timestamp=timestamp
                    )
                except Exception as e:
                    print(f"Ошибка сохранения {param_name} (строка {line_num}): {str(e)}")

if __name__ == '__main__':
    file_path = os.path.join(os.path.dirname(__file__), 'perm.txt')
    import_meteo_data(file_path)
    print("Импорт данных завершен.")
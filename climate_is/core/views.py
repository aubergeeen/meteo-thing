from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from stations.models import ParameterType
import datetime

def thingy(request):
    template = loader.get_template('core/dash.html')
    return HttpResponse(template.render())

def table_thing(request):
    template = loader.get_template('core/temp_table.html')
    return HttpResponse(template.render())

def choropleth(request):
    data = ParameterType.objects.all().values('param_id', 'name')  # получаем поля id и name всех станций из таблицы
    #template = loader.get_template('core/choropleth.html')
    return render(request, 'core/choropleth.html', {'params': data})
    #return HttpResponse(template.render())

def graph(request):
    #data = ParameterType.objects.all().values('param_id', 'name')  # получаем поля id и name всех станций из таблицы
    template = loader.get_template('core/graphs.html')
    #return render(request, 'core/choropleth.html', {'params': data})
    return HttpResponse(template.render())

def dud(request):
    template = loader.get_template('core/dud.html')
    return HttpResponse(template.render())

def choropleth_ver2(request):
    data = ParameterType.objects.all().values('param_id', 'name')  # получаем поля id и name всех станций из таблицы
    #template = loader.get_template('core/choropleth.html')
    return render(request, 'core/choropl_ver2.html', {'params': data})
    #return HttpResponse(template.render())



# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# import datetime

# class ClimateDataView(APIView):
#     def get(self, request):
#         # Generate dates for May 11 to June 10, 2025, in dd.mm format
#         dates = []
#         end_date = datetime.date(2025, 6, 10)
#         for i in range(30, -1, -1):
#             date = end_date - datetime.timedelta(days=i)
#             dates.append(date.strftime('%d.%m'))

#         # Realistic temperature data for Perm Krai (late spring/early summer)
#         climate_norm_temp = [
#             8.0, 8.2, 8.5, 8.8, 9.0, 9.3, 9.7, 10.0, 10.5, 11.0, 11.5,
#             12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5,
#             17.0, 17.5, 18.0, 18.3, 18.5, 18.7, 18.8, 19.0, 19.2, 19.5
#         ]
#         actual_temp = [
#             7.5, 8.0, 9.0, 7.8, 9.5, 10.0, 8.5, 11.0, 12.0, 10.5, 12.5,
#             13.0, 11.5, 14.0, 15.0, 13.5, 15.5, 16.0, 14.5, 17.0, 18.0,
#             16.5, 19.0, 20.0, 17.5, 18.0, 19.5, 17.0, 20.0, 21.0, 19.0
#         ]

#         # Realistic precipitation data for Perm Krai (mm)
#         # Climate norm: smoothed averages based on ~50 mm monthly total, ~1.6 mm/day
#         climate_norm_precip = [
#             1.5, 1.5, 1.6, 1.6, 1.5, 1.5, 1.7, 1.6, 1.5, 1.6, 1.5,
#             1.6, 1.5, 1.6, 1.7, 1.6, 1.5, 1.6, 1.5, 1.6, 1.5,
#             1.6, 1.7, 1.6, 1.5, 1.5, 1.6, 1.7, 1.6, 1.5, 1.6
#         ]
#         # Actual precipitation: varied, with dry days and occasional heavier rain
#         actual_precip = [
#             0.0, 0.5, 0.0, 3.0, 0.0, 0.2, 2.0, 0.0, 0.0, 4.0, 0.0,
#             1.5, 0.0, 0.0, 5.0, 0.0, 0.0, 1.0, 0.0, 2.5, 0.0,
#             0.0, 3.5, 0.0, 0.0, 0.8, 0.0, 6.0, 0.0, 0.0, 1.5
#         ]

#         data = {
#             'dates': dates,
#             'temperature': {
#                 'climate_norm': climate_norm_temp,
#                 'actual': actual_temp
#             },
#             'precipitation': {
#                 'climate_norm': climate_norm_precip,
#                 'actual': actual_precip
#             }
#         }

#         return Response(data, status=status.HTTP_200_OK)
    
# class MeasurementListView(APIView):
#     def get(self, request):
#         parameter = request.query_params.get("parameter", "effective_temp")
#         period = request.query_params.get("period", "8")
        
#         if parameter == "effective_temp" and period == "8":
#             measurements = [
#                 {"station": 1, "value": 16.5},
#                 {"station": 2, "value": 15.8},
#                 {"station": 3, "value": 16.0},
#                 {"station": 4, "value": 17.2},
#                 {"station": 5, "value": 18.0},
#                 {"station": 6, "value": 17.5},
#                 {"station": 7, "value": 15.5},
#                 {"station": 8, "value": 16.3},
#             ]
#         elif parameter == "min_humidity" and period == "2":
#             measurements = [
#                 {"station": 1, "value": 65},
#                 {"station": 2, "value": 68},
#                 {"station": 3, "value": 70},
#                 {"station": 4, "value": 62},
#                 {"station": 5, "value": 60},
#                 {"station": 6, "value": 63},
#                 {"station": 7, "value": 67},
#                 {"station": 8, "value": 66},
#             ]
#         else:
#             measurements = []  # Пустой ответ для неподдерживаемых комбинаций
#         return Response(measurements)

# class WeatherDataView(APIView):
#     def get(self, request):
#         station_id = request.query_params.get("station_id", "1")
#         time_step = request.query_params.get("time_step", "1w")
        
#         # Daily data for Station 1 (Пермь - Гайва)
#         daily_data = {
#             "1": [
#                 {"date": "14.06.2024", "temperature": 19.2, "humidity": 63, "precipitation": 1.5, "wind_speed": 3.4, "utci": 18.4, "wbgt": 20.6, "cwsi": 0.40, "heat_index": 19.8},
#                 {"date": "13.06.2024", "temperature": 19.0, "humidity": 64, "precipitation": 1.7, "wind_speed": 3.3, "utci": 18.2, "wbgt": 20.5, "cwsi": 0.39, "heat_index": 19.6},
#                 {"date": "12.06.2024", "temperature": 18.8, "humidity": 65, "precipitation": 1.4, "wind_speed": 3.2, "utci": 18.0, "wbgt": 20.3, "cwsi": 0.38, "heat_index": 19.4},
#                 {"date": "11.06.2024", "temperature": 18.6, "humidity": 66, "precipitation": 1.6, "wind_speed": 3.1, "utci": 17.9, "wbgt": 20.2, "cwsi": 0.37, "heat_index": 19.2},
#                 {"date": "10.06.2024", "temperature": 18.4, "humidity": 67, "precipitation": 1.8, "wind_speed": 3.0, "utci": 17.7, "wbgt": 20.1, "cwsi": 0.36, "heat_index": 19.0},
#                 {"date": "09.06.2024", "temperature": 18.7, "humidity": 65, "precipitation": 1.9, "wind_speed": 3.2, "utci": 17.8, "wbgt": 20.3, "cwsi": 0.38, "heat_index": 19.3},
#                 {"date": "08.06.2024", "temperature": 18.8, "humidity": 64, "precipitation": 2.0, "wind_speed": 3.3, "utci": 18.0, "wbgt": 20.3, "cwsi": 0.41, "heat_index": 19.4},
#                 {"date": "07.06.2024", "temperature": 18.3, "humidity": 66, "precipitation": 1.5, "wind_speed": 3.1, "utci": 17.7, "wbgt": 20.0, "cwsi": 0.39, "heat_index": 19.0},
#                 {"date": "06.06.2024", "temperature": 18.0, "humidity": 67, "precipitation": 1.3, "wind_speed": 3.0, "utci": 17.5, "wbgt": 19.9, "cwsi": 0.37, "heat_index": 18.8},
#                 {"date": "05.06.2024", "temperature": 17.8, "humidity": 68, "precipitation": 1.4, "wind_speed": 2.9, "utci": 17.3, "wbgt": 19.8, "cwsi": 0.36, "heat_index": 18.6},
#                 {"date": "04.06.2024", "temperature": 17.6, "humidity": 69, "precipitation": 1.2, "wind_speed": 2.8, "utci": 17.1, "wbgt": 19.7, "cwsi": 0.35, "heat_index": 18.4},
#                 {"date": "03.06.2024", "temperature": 17.4, "humidity": 70, "precipitation": 1.1, "wind_speed": 2.7, "utci": 16.9, "wbgt": 19.6, "cwsi": 0.34, "heat_index": 18.2},
#                 {"date": "02.06.2024", "temperature": 17.2, "humidity": 71, "precipitation": 1.0, "wind_speed": 2.6, "utci": 16.7, "wbgt": 19.5, "cwsi": 0.33, "heat_index": 18.0},
#                 {"date": "01.06.2024", "temperature": 17.5, "humidity": 68, "precipitation": 1.8, "wind_speed": 2.9, "utci": 16.8, "wbgt": 19.5, "cwsi": 0.32, "heat_index": 18.2}
#             ]
#         }

#         if station_id == "1" and time_step == "1d":
#             # Return daily data for Station 1 (Пермь - Гайва)
#             return Response(daily_data.get("1", []))
        
#         elif station_id == "2" and time_step == "1w":
#             # Weekly data for Station 2 (Пермь - Центр)
#             week_data = []
#             # Derive one week from daily data for consistency (01.06.2024 - 08.06.2024)
#             temp_daily = [
#                 {"date": "08.06.2024", "temperature": 19.3, "humidity": 61, "precipitation": 1.8, "wind_speed": 3.6, "utci": 18.5, "wbgt": 20.7, "cwsi": 0.37, "heat_index": 19.9},
#                 {"date": "07.06.2024", "temperature": 18.7, "humidity": 63, "precipitation": 1.2, "wind_speed": 3.4, "utci": 18.1, "wbgt": 20.2, "cwsi": 0.35, "heat_index": 19.5},
#                 {"date": "06.06.2024", "temperature": 18.5, "humidity": 64, "precipitation": 1.3, "wind_speed": 3.3, "utci": 17.9, "wbgt": 20.1, "cwsi": 0.36, "heat_index": 19.3},
#                 {"date": "05.06.2024", "temperature": 18.3, "humidity": 65, "precipitation": 1.4, "wind_speed": 3.2, "utci": 17.7, "wbgt": 20.0, "cwsi": 0.35, "heat_index": 19.1},
#                 {"date": "04.06.2024", "temperature": 18.1, "humidity": 66, "precipitation": 1.2, "wind_speed": 3.1, "utci": 17.5, "wbgt": 19.9, "cwsi": 0.34, "heat_index": 18.9},
#                 {"date": "03.06.2024", "temperature": 17.9, "humidity": 67, "precipitation": 1.1, "wind_speed": 3.0, "utci": 17.3, "wbgt": 19.8, "cwsi": 0.33, "heat_index": 18.7},
#                 {"date": "02.06.2024", "temperature": 17.7, "humidity": 68, "precipitation": 1.0, "wind_speed": 2.9, "utci": 17.1, "wbgt": 19.7, "cwsi": 0.32, "heat_index": 18.5},
#                 {"date": "01.06.2024", "temperature": 18.0, "humidity": 65, "precipitation": 1.5, "wind_speed": 3.2, "utci": 17.3, "wbgt": 19.8, "cwsi": 0.34, "heat_index": 18.7}
#             ]
#             # Calculate averages for 01.06.2024 - 08.06.2024
#             week_data.append({
#                 "date_range": "01.06.2024 - 08.06.2024",
#                 "temperature": sum(d["temperature"] for d in temp_daily) / len(temp_daily),
#                 "humidity": sum(d["humidity"] for d in temp_daily) / len(temp_daily),
#                 "precipitation": sum(d["precipitation"] for d in temp_daily),  # Sum for precipitation
#                 "wind_speed": sum(d["wind_speed"] for d in temp_daily) / len(temp_daily),
#                 "utci": sum(d["utci"] for d in temp_daily) / len(temp_daily),
#                 "wbgt": sum(d["wbgt"] for d in temp_daily) / len(temp_daily),
#                 "cwsi": sum(d["cwsi"] for d in temp_daily) / len(temp_daily),
#                 "heat_index": sum(d["heat_index"] for d in temp_daily) / len(temp_daily)
#             })
#             # Static data for previous weeks
#             week_data.extend([
#                 {"date_range": "25.05.2024 - 31.05.2024", "temperature": 17.8, "humidity": 68, "precipitation": 7.9, "wind_speed": 3.0, "utci": 17.0, "wbgt": 19.8, "cwsi": 0.32, "heat_index": 18.5},
#                 {"date_range": "18.05.2024 - 24.05.2024", "temperature": 16.5, "humidity": 70, "precipitation": 8.5, "wind_speed": 2.8, "utci": 16.0, "wbgt": 19.0, "cwsi": 0.33, "heat_index": 17.5},
#                 {"date_range": "11.05.2024 - 17.05.2024", "temperature": 15.2, "humidity": 72, "precipitation": 9.0, "wind_speed": 2.7, "utci": 15.0, "wbgt": 18.5, "cwsi": 0.34, "heat_index": 16.5},
#                 {"date_range": "04.05.2024 - 10.05.2024", "temperature": 14.0, "humidity": 75, "precipitation": 10.0, "wind_speed": 2.6, "utci": 14.0, "wbgt": 17.8, "cwsi": 0.35, "heat_index": 15.5},
#                 {"date_range": "27.04.2024 - 03.05.2024", "temperature": 12.8, "humidity": 78, "precipitation": 11.0, "wind_speed": 2.5, "utci": 13.0, "wbgt": 17.0, "cwsi": 0.36, "heat_index": 14.5},
#                 {"date_range": "20.04.2024 - 26.04.2024", "temperature": 11.5, "humidity": 80, "precipitation": 12.0, "wind_speed": 2.4, "utci": 12.0, "wbgt": 16.5, "cwsi": 0.37, "heat_index": 13.5},
#                 {"date_range": "13.04.2024 - 19.04.2024", "temperature": 10.2, "humidity": 82, "precipitation": 13.0, "wind_speed": 2.3, "utci": 11.0, "wbgt": 16.0, "cwsi": 0.38, "heat_index": 12.5}
#             ])
#             return Response(week_data)
        
#         else:
#             return Response([])  # Empty response for unsupported combinations

# from rest_framework.views import APIView
# from rest_framework.response import Response

# class GraphDataView(APIView):
#     def get(self, request):
#         tab = request.query_params.get("tab")
#         parameter = request.query_params.get("parameter")
#         year_start = int(request.query_params.get("year_start", 2020))
#         year_end = int(request.query_params.get("year_end", 2021))
#         threshold = float(request.query_params.get("threshold", 18)) if tab == "indexes" else None

#         # Define months for 2020–2021
#         base_months = [
#             'Янв 2020', 'Фев 2020', 'Мар 2020', 'Апр 2020', 'Май 2020', 'Июн 2020',
#             'Июл 2020', 'Авг 2020', 'Сен 2020', 'Окт 2020', 'Ноя 2020', 'Дек 2020',
#             'Янв 2021', 'Фев 2021', 'Мар 2021', 'Апр 2021', 'Май 2021', 'Июн 2021',
#             'Июл 2021', 'Авг 2021', 'Сен 2021', 'Окт 2021', 'Ноя 2021', 'Дек 2021'
#         ]
#         # Base temperature data (similar to template’s sinusoidal pattern)
#         base_temperatures = [
#             -5.2, -4.8, 0.5, 5.3, 10.8, 15.7, 20.2, 18.9, 13.4, 7.6, 1.2, -3.5,
#             -4.9, -4.5, 0.8, 5.6, 11.0, 16.0, 20.5, 19.2, 13.7, 7.9, 1.5, -3.2
#         ]
#         # Climate norm (smooth sinusoidal)
#         climate_norm = [
#             -5.0, -4.5, 0.0, 5.0, 10.5, 15.5, 20.0, 19.0, 13.5, 7.5, 1.0, -4.0,
#             -5.0, -4.5, 0.0, 5.0, 10.5, 15.5, 20.0, 19.0, 13.5, 7.5, 1.0, -4.0
#         ]

#         # Extend for 2022–2025 with slight variations
#         months = base_months[:]
#         temperatures = base_temperatures[:]
#         norm = climate_norm[:]
#         for year in range(2022, year_end + 1):
#             for month_idx, month_name in enumerate(['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']):
#                 months.append(f"{month_name} {year}")
#                 # Add small random variation to base temperature
#                 temp_variation = (month_idx % 12) * 0.3 - 0.15  # Simple variation
#                 temperatures.append(base_temperatures[month_idx] + temp_variation)
#                 norm.append(climate_norm[month_idx])

#         # Filter by year range
#         filtered_data = [
#             (m, t, n) for m, t, n in zip(months, temperatures, norm)
#             if year_start <= int(m.split()[-1]) <= year_end
#         ]
#         filtered_months, filtered_temperatures, filtered_norm = zip(*filtered_data) if filtered_data else ([], [], [])

#         if tab == "statistics" and parameter == "temp":
#             return Response({
#                 "months": list(filtered_months),
#                 "temperatures": list(filtered_temperatures),
#                 "climate_norm": list(filtered_norm)
#             })
#         elif tab == "indexes" and parameter == "cdd":
#             # Calculate CDD: sum of (monthly avg temp - threshold) for months where temp > threshold
#             cdd_values = [
#                 max(0, temp - threshold) for temp in filtered_temperatures
#             ]
#             return Response({
#                 "months": list(filtered_months),
#                 "cdd": cdd_values,
#                 "climate_norm": [0] * len(filtered_months)  # No norm for CDD
#             })
#         else:
#             return Response({"months": [], "data": [], "climate_norm": []})

def graphs_view(request):
    current_year = datetime.datetime.now().year
    years = list(range(current_year - 10, current_year + 1))  # От 2010 до 2025
    return render(request, 'core/graphs.html', {'years': years})
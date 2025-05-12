from django.db.models import Avg, Max, Min, FloatField
from django.db.models.functions import Coalesce, TruncWeek, TruncDay, TruncMonth, TruncYear

# Подсчитывает агрегаты по заданным интервалам для заданного параметра
def time_aggregates(queryset, param_type, aggregate_func='avg', period='week'):

    # получаем Trunc и агрегат. ф-ии в соответсвии с переданым параметром
    aggregates = { 'avg': Avg, 'min': Min, 'max': Max, }
    period_functions = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear, }
    
    # валидация 
    if aggregate_func.lower() not in aggregates:
        raise ValueError(f"Unsupported aggregate function: {aggregate_func}")
    if period.lower() not in period_functions:
        raise ValueError(f"Unsupported time period: {period}")
    
    trunc_func = period_functions[period.lower()]
    aggregation = aggregates[aggregate_func.lower()]
    
    # собираем запрос
    return (
        queryset                                                
        .filter(sensor__sensor_model__param_type=param_type)    # where и inner join'ы
        .annotate(time_period=trunc_func('time'))               # date_trunc('time) as time_period
        .values('time_period')                                  # group by time_period (returns a QuerySet that returns dictionaries
        .annotate(value=aggregation('value'))                   # avg('value') as 'value'                 
        .order_by('time_period')                                # сортировка
    )
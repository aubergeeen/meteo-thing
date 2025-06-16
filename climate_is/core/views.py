from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from stations.models import ParameterType
import datetime
from django.utils import timezone

def dud(request):
    template = loader.get_template('core/dud.html')
    return HttpResponse(template.render())

def choropleth_ver2(request):
    months = [{'value': i, 'name': name} for i, name in enumerate(['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'], 1)]
    years = range(2005, timezone.now().year + 1)
    data = ParameterType.objects.all().values('param_id', 'name')  # получаем поля id и name всех станций из таблицы
    #template = loader.get_template('core/choropleth.html')
    return render(request, 'core/choropl_ver2.html', {'params': data, 'months':months, 'years':years})
    #return HttpResponse(template.render())

def graphs_view(request):
    current_year = datetime.datetime.now().year
    years = list(range(current_year - 10, current_year + 1))  # От 2010 до 2025
    return render(request, 'core/graphs.html', {'years': years})
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from stations.models import ParameterType

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

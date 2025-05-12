from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def thingy(request):
    template = loader.get_template('core/dash.html')
    return HttpResponse(template.render())

def table_thing(request):
    template = loader.get_template('core/temp_table.html')
    return HttpResponse(template.render())
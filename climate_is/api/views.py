from rest_framework.response import Response
from rest_framework.decorators import api_view
from readings.models import Reading
from .serializers import ReadingSerializer

@api_view(['GET'])  
def getReading(request):
    readings = Reading.objects.all()
    serializer = ReadingSerializer(readings, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def addReading(request):
    serializer = ReadingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)
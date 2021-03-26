from rest_framework import viewsets 
from rest_framework import status, permissions
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import permissions
from django.db.models import Q

from scilicium_django_react.datasets.models import Dataset, Loom
from scilicium_django_react.datasets.api.serializers import DatasetSerializer, LoomSerializer
from scilicium_django_react.users.models import User
from scilicium_django_react.utils.loom_reader import *
from scilicium_django_react.utils.chartjsCreator import *
from scilicium_django_react.utils.plotlyCreator import *


class DatasetViewSet(viewsets.ModelViewSet):

    serializer_class = DatasetSerializer
    queryset = Dataset.objects.all()
    lookup_field = 'datasetId'
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, permission_classes=[permissions.AllowAny],url_path='filters', url_name='filters')
    def filters(self, request, *args, **kwargs):
        dataset = self.get_object()
        if dataset.status == "PUBLIC" or dataset.created_by == self.request.user:
            key = request.GET.get('key', None)
            value = request.GET.get('value', None)

            data = get_object_or_404(Loom,id=dataset.loom.id)
            if key == "row":
                values = get_ra(data.file.path,key=value,unique=True)
                return  Response({"values":values}, status=status.HTTP_200_OK)
            if key == "col":
                values = get_ca(data.file.path,key=value,unique=True)
                return  Response({"values":values}, status=status.HTTP_200_OK)
            else :
                return Response('Key value not recognize', status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)
        else :
            return Response('Your are not allowed to access this ressource', status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, permission_classes=[permissions.AllowAny],url_path='view', url_name='view')
    def view(self, request, *args, **kwargs):
        dataset = self.get_object()
        if dataset.status == "PUBLIC" or dataset.created_by == self.request.user:
            serializer = DatasetSerializer(dataset)
            return Response(serializer.data)
        else :
            return Response('Your are not allowed to access this ressource', status=status.HTTP_403_FORBIDDEN)
    
    

class LoomViewSet(viewsets.ModelViewSet):
    serializer_class = LoomSerializer
    queryset = Loom.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
class GetLoomPlots(APIView):
    """
        Associated view for the REACT CellCountComponent component
        User request validation (data public or user == data owner)
        [GET] --> data id
        [RESPONSE] --> HTTP_403_Forbidden (data private && user not owner)
        [RESPONSE] --> HTTP_200_OK  (data public | user owner)
        [RSPONSE][data] : {
            count : int(numberOfcells) or int(numberOfSamples),
            name : str(data.name)
        }

    """
    # Allow anyone to access
    # For test only
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def get(self, request, *args, **kw):

        # Process any get params that you may need
        # If you don't need to process get params,
        # you can skip this part

        data_id = request.GET.get('id', None)
        attrs = request.GET.get('attrs', None)
        style = request.GET.get('style', None)

        # Get data
        data = get_object_or_404(Loom,id=data_id)

        # Data status check + user ownership == TO DO check status from dataset
        #if data.status == "PRIVATE" and data.created_by != self.request.user :
        #    response = Response({"msg":"You are not allowed to access this ressource"}, status=status.HTTP_403_FORBIDDEN)
        #    return response
        
        
        response_data = dict()
        response_data["name"] = data.name
        response_data["classes"] = data.classes

        if attrs == 'undefined' :
            attrs = [response_data["classes"][0]]
        else:
            attrs = [attrs]
        if style =="scatter":
            response_data['chart'] = json_scatter(data.file.path)
            response_data['style'] = "scatter"

            response = Response(response_data, status=status.HTTP_200_OK)
            return response
        else :
            data = json.loads(json_component_chartjs(data.file.path,style=style,attrs=attrs))
            response_data['chart'] = data["chart"]
            response_data['style'] = data["style"]

            response = Response(response_data, status=status.HTTP_200_OK)
            return response
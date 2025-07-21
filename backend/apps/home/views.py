# from django.shortcuts import render
# from rest_framework import generics, status
# from rest_framework.response import Response
# import requests
# from apps.home.services import RecipeService
# from apps.home.models import RecipeModel
# from apps.home.serializers import RecipeSerializer


# class RecipeListCreateApiView(generics.ListCreateAPIView):
#   serializer_class=RecipeSerializer
#   def get_queryset(self):
#       return super().get_queryset()
    
#   def create(self, request, *args, **kwargs):
#     try:
#       result = RecipeService.create_recipe(request.data)
#       if 'recipe_id' in result:
#         return Response(result, status=status.HTTP_201_CREATED)
#       else:
#         return Response(result, status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#       return Response({
#         "status":status.HTTP_400_BAD_REQUEST,
#         "error": str(e)
#       })
    
  



# class DemoRetriveApiView(generics.RetrieveAPIView):
#   def get(self, request, *args, **kwargs):
#       return Response({
#         "data": "hello"
#       })




import logging
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from apps.home.services import RecipeService
from apps.home.models import RecipeModel
from apps.home.serializers import RecipeListSerializer, RecipeDetailSerializer

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RecipeListCreateApiView(generics.ListCreateAPIView):
    """
    List all recipes or create a new recipe
    """
    serializer_class = RecipeListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['recipe_type']
    search_fields = ['recipe_name', 'recipe_description']
    ordering_fields = ['created_at', 'recipe_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Optimized queryset for list view"""
        return RecipeModel.objects.filter(is_active=True).select_related().only(
            'recipe_id', 'recipe_name', 'recipe_image',
            'recipe_slug', 'recipe_type', 'created_at'
        )
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.request.method == 'POST':
            return RecipeDetailSerializer
        return RecipeListSerializer
    
    def list(self, request, *args, **kwargs):
        """Custom list method with service layer"""
        try:
            filters = {
                'recipe_type': request.query_params.get('recipe_type'),
                'search': request.query_params.get('search'),
            }
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            result = RecipeService.get_all_recipes(filters)
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error in recipe list view: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """Create recipe using service layer"""
        try:
            result = RecipeService.create_recipe(request.data)
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error in recipe creation: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecipeRetrieveUpdateDestroyApiView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a recipe instance
    """
    serializer_class = RecipeDetailSerializer
    lookup_field = 'recipe_id'
    
    def get_queryset(self):
        return RecipeModel.objects.filter(is_active=True)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve recipe using service layer"""
        try:
            recipe_id = kwargs.get('recipe_id')
            result = RecipeService.get_recipe_by_id(recipe_id)
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error retrieving recipe: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """Update recipe using service layer"""
        try:
            recipe_id = kwargs.get('recipe_id')
            result = RecipeService.update_recipe(recipe_id, request.data)
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_200_OK)
            elif 'not found' in result['message']:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating recipe: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete recipe using service layer"""
        try:
            recipe_id = kwargs.get('recipe_id')
            result = RecipeService.delete_recipe(recipe_id)
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error deleting recipe: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
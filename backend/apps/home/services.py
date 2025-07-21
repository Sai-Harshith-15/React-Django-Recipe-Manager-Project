# from apps.home.models import RecipeModel
# from apps.home.serializers import RecipeSerializer


# class RecipeService:
#   @staticmethod
#   def create_recipe(data):
#     try:
#       recipe_serializer = RecipeSerializer(data=data)
#       if recipe_serializer.is_valid():
#         recipe = recipe_serializer.save()
#         return RecipeSerializer(recipe).data
#       else:
#         return recipe_serializer.errors
#     except Exception as e:
#       print(f"error in creating recipe {e}")

import logging
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.cache import cache
from django.utils.text import slugify
from apps.home.models import RecipeModel
from apps.home.serializers import (
    RecipeSerializer, 
    RecipeListSerializer, 
    RecipeDetailSerializer
)

logger = logging.getLogger(__name__)


class RecipeService:
    """Service layer for Recipe business logic"""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def get_all_recipes(filters: Dict[str, Any] = None, page_size: int = 20) -> Dict[str, Any]:
        """
        Get all recipes with optional filtering
        """
        try:
            cache_key = f"recipes_list_{hash(str(filters))}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.info("Returning cached recipe list")
                return cached_data
            
            queryset = RecipeModel.objects.filter(is_active=True)
            
            # Apply filters
            if filters:
                if 'recipe_type' in filters:
                    queryset = queryset.filter(recipe_type=filters['recipe_type'])
                if 'search' in filters:
                    queryset = queryset.filter(
                        recipe_name__icontains=filters['search']
                    )
            
            # Optimize query
            queryset = queryset.select_related().only(
                'recipe_id', 'recipe_name', 'recipe_image',
                'recipe_slug', 'recipe_type', 'created_at'
            )
            
            serializer = RecipeListSerializer(queryset, many=True)
            result = {
                'status': 'success',
                'data': serializer.data,
                'count': queryset.count()
            }
            
            cache.set(cache_key, result, RecipeService.CACHE_TIMEOUT)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching recipes: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to fetch recipes',
                'error': str(e)
            }
    
    @staticmethod
    def get_recipe_by_id(recipe_id: str) -> Dict[str, Any]:
        """
        Get single recipe by ID
        """
        try:
            cache_key = f"recipe_{recipe_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return cached_data
            
            recipe = RecipeModel.objects.get(
                recipe_id=recipe_id, 
                is_active=True
            )
            
            serializer = RecipeDetailSerializer(recipe)
            result = {
                'status': 'success',
                'data': serializer.data
            }
            
            cache.set(cache_key, result, RecipeService.CACHE_TIMEOUT)
            return result
            
        except RecipeModel.DoesNotExist:
            return {
                'status': 'error',
                'message': 'Recipe not found'
            }
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to fetch recipe',
                'error': str(e)
            }
    
    @staticmethod
    @transaction.atomic
    def create_recipe(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new recipe with business logic
        """
        try:
            # Validate and create
            serializer = RecipeSerializer(data=data)
            
            if not serializer.is_valid():
                return {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }
            
            # Additional business logic
            recipe_name = serializer.validated_data['recipe_name']
            slug = slugify(recipe_name)
            
            # Ensure unique slug
            counter = 1
            original_slug = slug
            while RecipeModel.objects.filter(recipe_slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            serializer.validated_data['recipe_slug'] = slug
            recipe = serializer.save()
            
            # Clear cache
            cache.delete_pattern("recipes_list_*")
            
            logger.info(f"Recipe created successfully: {recipe.recipe_id}")
            
            return {
                'status': 'success',
                'message': 'Recipe created successfully',
                'data': RecipeDetailSerializer(recipe).data
            }
            
        except Exception as e:
            logger.error(f"Error creating recipe: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to create recipe',
                'error': str(e)
            }
    
    @staticmethod
    @transaction.atomic
    def update_recipe(recipe_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing recipe
        """
        try:
            recipe = RecipeModel.objects.get(
                recipe_id=recipe_id,
                is_active=True
            )
            
            serializer = RecipeSerializer(recipe, data=data, partial=True)
            
            if not serializer.is_valid():
                return {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }
            
            # Handle slug update if name changed
            if 'recipe_name' in data:
                new_slug = slugify(data['recipe_name'])
                if new_slug != recipe.recipe_slug:
                    counter = 1
                    original_slug = new_slug
                    while RecipeModel.objects.filter(
                        recipe_slug=new_slug
                    ).exclude(recipe_id=recipe_id).exists():
                        new_slug = f"{original_slug}-{counter}"
                        counter += 1
                    serializer.validated_data['recipe_slug'] = new_slug
            
            updated_recipe = serializer.save()
            
            # Clear cache
            cache.delete(f"recipe_{recipe_id}")
            cache.delete_pattern("recipes_list_*")
            
            logger.info(f"Recipe updated successfully: {recipe_id}")
            
            return {
                'status': 'success',
                'message': 'Recipe updated successfully',
                'data': RecipeDetailSerializer(updated_recipe).data
            }
            
        except RecipeModel.DoesNotExist:
            return {
                'status': 'error',
                'message': 'Recipe not found'
            }
        except Exception as e:
            logger.error(f"Error updating recipe {recipe_id}: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to update recipe',
                'error': str(e)
            }
    
    @staticmethod
    @transaction.atomic
    def delete_recipe(recipe_id: str) -> Dict[str, Any]:
        """
        Soft delete recipe (set is_active=False)
        """
        try:
            recipe = RecipeModel.objects.get(
                recipe_id=recipe_id,
                is_active=True
            )
            
            recipe.is_active = False
            recipe.save()
            
            # Clear cache
            cache.delete(f"recipe_{recipe_id}")
            cache.delete_pattern("recipes_list_*")
            
            logger.info(f"Recipe deleted successfully: {recipe_id}")
            
            return {
                'status': 'success',
                'message': 'Recipe deleted successfully'
            }
            
        except RecipeModel.DoesNotExist:
            return {
                'status': 'error',
                'message': 'Recipe not found'
            }
        except Exception as e:
            logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to delete recipe',
                'error': str(e)
            }
from apps.home.models import RecipeModel, IngredientsModel
from rest_framework import serializers
from django.utils.text import slugify

# class RecipeSerializer(serializers.ModelSerializer):
#   class Meta:
#     model = RecipeModel
#     fields = '__all__'

class RecipeSerializer(serializers.ModelSerializer):
    recipe_slug = serializers.SlugField(read_only=True)
    
    class Meta:
        model = RecipeModel
        fields = [
            'recipe_id', 'recipe_name', 'recipe_description',
            'recipe_image', 'recipe_slug', 'recipe_type',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['recipe_id', 'created_at', 'updated_at']
        
    def validate_recipe_name(self, value):
        """Custom validation for recipe name"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Recipe name must be at least 3 characters long."
            )
        return value.strip().title()
        
    def validate(self, attrs):
        """Cross-field validation"""
        recipe_name = attrs.get('recipe_name')
        if recipe_name:
            slug = slugify(recipe_name)
            # Check for duplicate slug during creation
            if not self.instance and RecipeModel.objects.filter(recipe_slug=slug).exists():
                raise serializers.ValidationError({
                    'recipe_name': 'A recipe with this name already exists.'
                })
        return attrs

class IngredientsSerializer(serializers.ModelSerializer):
  class Meta:
    model = IngredientsModel
    fields = '__all__'


class RecipeListSerializer(serializers.ModelSerializer):
    """Optimized serializer for list views"""
    class Meta:
        model = RecipeModel
        fields = [
            'recipe_id', 'recipe_name', 'recipe_image',
            'recipe_slug', 'recipe_type', 'created_at'
        ]
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['ingredients'] = IngredientsSerializer(instance.recipe_ingredients.all(), many=True).data
        
        return data
        
        


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for retrieve views"""
    class Meta:
        model = RecipeModel
        fields = '__all__'
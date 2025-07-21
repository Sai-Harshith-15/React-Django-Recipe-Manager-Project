from django.db import models
import uuid
from django.core.validators import MinLengthValidator
from django.utils.text import slugify

# class RecipeModel(models.Model):
#   recipe_id = models.UUIDField(primary_key=True, default=uuid.uuid4(), unique=True)
#   recipe_name = models.CharField(max_length=100, db_index=True)
#   recipe_description = models.TextField()
#   recipe_image = models.ImageField(upload_to="recipe/")
#   recipe_slug = models.SlugField(unique=True)
#   recipe_type = models.CharField(max_length=100, choices=(("Veg", "veg"), ("Non-Veg", "non-veg")))
#   created_at = models.DateTimeField(auto_now_add=True)
#   updated_at = models.DateTimeField(auto_now=True)
  
#   class Meta:
#     db_table = 'recipes_master'
   
class RecipeModel(models.Model):
    RECIPE_TYPE_CHOICES = [
        ('VEG', 'Vegetarian'),
        ('NON_VEG', 'Non-Vegetarian'),
        ('VEGAN', 'Vegan'),
    ]
    
    recipe_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    recipe_name = models.CharField(
        max_length=100, 
        db_index=True,
        validators=[MinLengthValidator(3)]
    )
    recipe_description = models.TextField(
        validators=[MinLengthValidator(10)]
    )
    recipe_image = models.ImageField(
        upload_to="recipes/%Y/%m/",
        null=True,
        blank=True
    )
    recipe_slug = models.SlugField(
        unique=True,
        max_length=120,
        db_index=True
    )
    recipe_type = models.CharField(
        max_length=20,
        choices=RECIPE_TYPE_CHOICES,
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipes_master'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipe_type', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
        ]
        
    def save(self, *args, **kwargs):
        if not self.recipe_slug:
            self.recipe_slug = slugify(self.recipe_name)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.recipe_name
  
  
class IngredientsModel(models.Model):
  ingredient_id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
  recipe = models.ForeignKey(RecipeModel, on_delete=models.CASCADE, related_name='recipe_ingredients')
  ingredient_name = models.CharField(max_length=100)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  
  class Meta:
    db_table = 'ingredients'
    
  def __str__(self):
        return f"{self.recipe.recipe_name} - {self.ingredient_name}"
  
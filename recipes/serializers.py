from rest_framework import serializers
from .translation_utils import translate_text
from .models import (
    Category, MealType, Recipe,
    Ingredient, Instruction,
    MealPlan, ShoppingListItem,
    RecipeRating
)

# CATEGORY
class CategorySerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang', 'en')
        data['name'] = translate_text(data['name'], lang)
        return data
    class Meta:
        model = Category
        fields = ['id', 'name']

# MEAL TYPE
class MealTypeSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang', 'en')
        data['name'] = translate_text(data['name'], lang)
        return data
    class Meta:
        model = MealType
        fields = ['id', 'name']

# INGREDIENT (autocomplete uchun name + id yetarli)
class IngredientSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang', 'en')
        for field in ['name', 'amount', 'unit', 'preparation']:
            value = data.get(field)
            if value:
                data[field] = translate_text(value, lang)
        return data
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'amount', 'unit', 'preparation']

# Faqat name va id uchun (autocomplete/search API uchun)
class IngredientNameSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang', 'en')
        data['name'] = translate_text(data['name'], lang)
        return data
    class Meta:
        model = Ingredient
        fields = ['id', 'name']

# INSTRUCTION
class InstructionSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang', 'en')
        data['description'] = translate_text(data['description'], lang)
        return data
    class Meta:
        model = Instruction
        fields = ['id', 'step_number', 'description']

# RECIPE
class RecipeSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        source='categories'
    )
    ingredients = IngredientSerializer(many=True)
    instructions = InstructionSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang', 'en')
        data['name'] = translate_text(data['name'], lang)
        data['description'] = translate_text(data['description'], lang)
        for cat in data.get('categories', []):
            cat['name'] = translate_text(cat['name'], lang)
        for ing in data.get('ingredients', []):
            for field in ['name', 'amount', 'unit', 'preparation']:
                value = ing.get(field)
                if value:
                    ing[field] = translate_text(value, lang)
        for step in data.get('instructions', []):
            step['description'] = translate_text(step['description'], lang)
        return data

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'categories', 'category_ids', 'description', 'image',
            'prep_time', 'cook_time', 'servings', 'healthy', #'tags',
            'calories', 'protein', 'fats', 'carbs',
            'ingredients', 'instructions'
        ]

    def create(self, validated_data):
        categories_data = validated_data.pop('categories', [])
        ingredients_data = validated_data.pop('ingredients')
        instructions_data = validated_data.pop('instructions')
        recipe = Recipe.objects.create(**validated_data)
        if categories_data:
            recipe.categories.set(categories_data)
        for ing in ingredients_data:
            Ingredient.objects.create(recipe=recipe, **ing)
        for step in instructions_data:
            Instruction.objects.create(recipe=recipe, **step)
        return recipe

    def update(self, instance, validated_data):
        categories_data = validated_data.pop('categories', None)
        ingredients_data = validated_data.pop('ingredients', None)
        instructions_data = validated_data.pop('instructions', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if categories_data is not None:
            instance.categories.set(categories_data)
        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ing in ingredients_data:
                Ingredient.objects.create(recipe=instance, **ing)
        if instructions_data is not None:
            instance.instructions.all().delete()
            for step in instructions_data:
                Instruction.objects.create(recipe=instance, **step)
        return instance

    def validate(self, data):
        if 'ingredients' in data and not data['ingredients']:
            raise serializers.ValidationError("Recipe must have at least one ingredient.")
        if 'instructions' in data and not data['instructions']:
            raise serializers.ValidationError("Recipe must have at least one instruction.")
        return data

# MEAL PLAN
class MealPlanSerializer(serializers.ModelSerializer):
    meal_type = MealTypeSerializer(read_only=True)
    meal_type_id = serializers.PrimaryKeyRelatedField(
        queryset=MealType.objects.all(),
        source='meal_type',
        write_only=True
    )
    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        source='recipe',
        write_only=True
    )

    class Meta:
        model = MealPlan
        fields = [
            'id', 'user', 'recipe', 'recipe_id',
            'meal_type', 'meal_type_id', 'scheduled_time'
        ]
        read_only_fields = ['user', 'recipe', 'meal_type']

    def create(self, validated_data):
        user = self.context['request'].user
        return MealPlan.objects.create(user=user, **validated_data)

# SHOPPING LIST ITEM
class ShoppingListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingListItem
        fields = ['id', 'name', 'amount', 'unit', 'checked']

# RECIPE RATING
class RecipeRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeRating
        fields = ['id', 'user', 'recipe', 'rating', 'comment', 'created']
        read_only_fields = ['user', 'recipe', 'created']

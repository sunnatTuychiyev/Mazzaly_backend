import datetime
from rest_framework import serializers
from .models import (
    Category, MealType, Recipe,
    Ingredient, Instruction,
    MealPlan, ShoppingListItem,
    RecipeRating,
    RecipeSubmission,
    UserRecipe,
)

# CATEGORY
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_uz', 'name_ru']
        extra_kwargs = {
            'name_uz': {'write_only': True, 'required': True},
            'name_ru': {'write_only': True, 'required': True},
        }

    def create(self, validated_data):
        name_uz = validated_data.pop('name_uz')
        name_ru = validated_data.pop('name_ru')
        return Category.objects.create(name=name_uz, name_uz=name_uz, name_ru=name_ru, **validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        # remove write-only fields
        data.pop('name_uz', None)
        data.pop('name_ru', None)
        if lang == 'ru':
            if instance.name_ru:
                data['name'] = instance.name_ru
            elif instance.name_uz:
                from .translation_utils import translate_text
                trans = translate_text(instance.name_uz, 'ru', 'uz')
                data['name'] = trans or instance.name_uz or instance.name
            else:
                data['name'] = instance.name
        else:
            if instance.name_uz:
                data['name'] = instance.name_uz
            elif instance.name_ru:
                from .translation_utils import translate_text
                trans = translate_text(instance.name_ru, 'uz', 'ru')
                data['name'] = trans or instance.name_ru or instance.name
            else:
                data['name'] = instance.name
        return data

# MEAL TYPE
class MealTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealType
        fields = ['id', 'name']

# INGREDIENT (autocomplete uchun name + id yetarli)
class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'name_uz', 'name_ru', 'amount', 'unit', 'unit_uz', 'unit_ru', 'preparation']
        extra_kwargs = {
            'name_uz': {'write_only': True, 'required': True},
            'name_ru': {'write_only': True, 'required': True},
            'unit_uz': {'write_only': True, 'required': False, 'allow_blank': True},
            'unit_ru': {'write_only': True, 'required': False, 'allow_blank': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        if lang == 'ru':
            data['name'] = instance.name_ru or instance.name
            data['unit'] = instance.unit_ru or instance.unit
        else:
            data['name'] = instance.name_uz or instance.name
            data['unit'] = instance.unit_uz or instance.unit
        # remove write-only translation fields from output
        data.pop('unit_uz', None)
        data.pop('unit_ru', None)
        data.pop('name_uz', None)
        data.pop('name_ru', None)
        return data

# Faqat name va id uchun (autocomplete/search API uchun)
class IngredientNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        if lang == 'ru':
            data['name'] = instance.name_ru or instance.name
        else:
            data['name'] = instance.name_uz or instance.name
        return data

# INSTRUCTION
class InstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instruction
        fields = ['id', 'step_number', 'description', 'description_uz', 'description_ru']
        extra_kwargs = {
            'description_uz': {'write_only': True, 'required': True},
            'description_ru': {'write_only': True, 'required': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        if lang == 'ru':
            data['description'] = instance.description_ru or instance.description
        else:
            data['description'] = instance.description_uz or instance.description
        data.pop('description_uz', None)
        data.pop('description_ru', None)
        return data

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

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'name_uz', 'name_ru', 'categories', 'category_ids', 'description', 'description_uz', 'description_ru', 'image',
            'prep_time', 'cook_time', 'servings', 'subscription_plan', 'healthy',
            'premium', 'calories', 'protein', 'fats', 'carbs',
            'ingredients', 'instructions'
        ]
        extra_kwargs = {
            'name_uz': {'write_only': True, 'required': True},
            'name_ru': {'write_only': True, 'required': True},
            'description_uz': {'write_only': True, 'required': True},
            'description_ru': {'write_only': True, 'required': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        if lang == 'ru':
            data['name'] = instance.name_ru or instance.name
            data['description'] = instance.description_ru or instance.description
        else:
            data['name'] = instance.name_uz or instance.name
            data['description'] = instance.description_uz or instance.description
        data.pop('name_uz', None)
        data.pop('name_ru', None)
        data.pop('description_uz', None)
        data.pop('description_ru', None)
        return data

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


class RecipeCardSerializer(serializers.ModelSerializer):
    """Simplified recipe info for listing cards."""
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'categories', 'description', 'image',
            'prep_time', 'cook_time', 'subscription_plan', 'views'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get('lang')
        if lang == 'ru':
            data['name'] = instance.name_ru or instance.name
            data['description'] = instance.description_ru or instance.description
        else:
            data['name'] = instance.name_uz or instance.name
            data['description'] = instance.description_uz or instance.description
        return data

# MEAL PLAN
class MealPlanSerializer(serializers.ModelSerializer):
    meal_type = MealTypeSerializer(read_only=True)
    meal_type_id = serializers.PrimaryKeyRelatedField(
        queryset=MealType.objects.all(),
        source='meal_type',
        write_only=True,
        required=False
    )
    type = serializers.CharField(write_only=True, required=False)
    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        source='recipe',
        write_only=True,
        required=False,
        allow_null=True
    )
    date = serializers.DateField(write_only=True)
    time = serializers.TimeField(write_only=True)
    custom_meal = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = MealPlan
        fields = [
            'id', 'user', 'recipe', 'recipe_id',
            'meal_type', 'meal_type_id', 'type',
            'scheduled_time', 'date', 'time', 'custom_meal'
        ]
        read_only_fields = ['user', 'recipe', 'meal_type', 'scheduled_time']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data.pop('user', None)
        meal_type_obj = validated_data.pop('meal_type', None)
        meal_type_name = validated_data.pop('type', None)
        if meal_type_name and not meal_type_obj:
            meal_type_obj = MealType.objects.filter(
                name__iexact=meal_type_name
            ).first()
            if not meal_type_obj:
                meal_type_obj = MealType.objects.create(name=meal_type_name)
        recipe_obj = validated_data.get('recipe')
        date = validated_data.pop('date')
        time = validated_data.pop('time')
        scheduled_time = datetime.datetime.combine(date, time)
        return MealPlan.objects.create(
            user=user,
            meal_type=meal_type_obj,
            scheduled_time=scheduled_time,
            **validated_data
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['date'] = instance.scheduled_time.date().isoformat()
        data['time'] = instance.scheduled_time.time().strftime('%H:%M')
        data['type'] = instance.meal_type.name if instance.meal_type else None
        lang = self.context.get('lang')
        if lang:
            if data['type']:
                from .translation_utils import translate_text
                trans = translate_text(data['type'], lang)
                if trans:
                    data['type'] = trans
            if instance.recipe:
                data['recipe'] = RecipeSerializer(instance.recipe, context=self.context).data
        return data

# SHOPPING LIST ITEM
class ShoppingListItemSerializer(serializers.ModelSerializer):
    amount = serializers.CharField(required=False, allow_blank=True, default="")
    unit = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = ShoppingListItem
        fields = ['id', 'name', 'amount', 'unit', 'checked']

# RECIPE RATING
class RecipeRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeRating
        fields = ['id', 'user', 'recipe', 'rating', 'comment', 'created']
        read_only_fields = ['user', 'recipe', 'created']

# RECIPE SUBMISSION
class IngredientInputSerializer(serializers.Serializer):
    name_uz = serializers.CharField()
    name_ru = serializers.CharField()
    amount = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit_uz = serializers.CharField(required=False, allow_blank=True, default="")
    unit_ru = serializers.CharField(required=False, allow_blank=True, default="")
    preparation = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        attrs.setdefault("name", attrs.get("name_uz", ""))
        attrs.setdefault("unit", attrs.get("unit_uz", ""))
        return attrs


class InstructionInputSerializer(serializers.Serializer):
    step_number = serializers.IntegerField()
    description_uz = serializers.CharField()
    description_ru = serializers.CharField()

    def validate(self, attrs):
        attrs.setdefault("description", attrs.get("description_uz", ""))
        return attrs


class RecipeSubmissionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    ingredients = IngredientInputSerializer(many=True, required=False, default=list)
    instructions = InstructionInputSerializer(
        many=True, required=False, default=list, source="steps"
    )
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, required=False
    )

    class Meta:
        model = RecipeSubmission
        fields = [
            "id",
            "name",
            "name_uz",
            "name_ru",
            "description",
            "description_uz",
            "description_ru",
            "prep_time",
            "cook_time",
            "servings",
            "subscription_plan",
            "healthy",
            "calories",
            "protein",
            "fats",
            "carbs",
            "categories",
            "ingredients",
            "instructions",
            "status",
            "moderator_note",
            "image",
            "created_at",
        ]
        read_only_fields = ["status", "moderator_note", "image", "created_at"]
        extra_kwargs = {
            "name_uz": {"required": True, "write_only": True},
            "name_ru": {"required": True, "write_only": True},
            "description_uz": {"required": True, "write_only": True},
            "description_ru": {"required": True, "write_only": True},
        }

    def get_image(self, obj):
        first = obj.images.first()
        return first.image.url if first else None

    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        submission = RecipeSubmission.objects.create(**validated_data)
        if categories:
            submission.categories.set(categories)
        return submission

    def validate(self, attrs):
        attrs["name"] = attrs.get("name_uz", attrs.get("name", ""))
        attrs["description"] = attrs.get("description_uz", attrs.get("description", ""))
        return attrs


# SIMPLE USER RECIPE SERIALIZER
class UserRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRecipe
        fields = ["id", "title", "image", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

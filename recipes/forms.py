from django import forms


MEAL_CHOICES = [
    ("breakfast", "Breakfast"),
    ("lunch", "Lunch"),
    ("dinner", "Dinner"),
]


class EdamamImportForm(forms.Form):
    count = forms.IntegerField(min_value=1, label="Number of recipes")
    query = forms.CharField(
        label="Ingredient or dish",
        initial="egg",
        required=False,
        help_text="Search term used when fetching recipes",
    )
    meal_type = forms.ChoiceField(
        choices=MEAL_CHOICES,
        label="Meal type",
        initial="breakfast",
    )


class SpoonacularImportForm(forms.Form):
    count = forms.IntegerField(min_value=1, label="Number of recipes")
    tags = forms.CharField(
        label="Recipe tags",
        required=False,
        help_text="Comma separated tags like 'vegetarian,dessert'",
    )
    meal_type = forms.ChoiceField(
        choices=MEAL_CHOICES,
        label="Meal type",
        initial="breakfast",
    )

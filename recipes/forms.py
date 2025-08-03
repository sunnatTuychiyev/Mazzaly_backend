from django import forms


class EdamamImportForm(forms.Form):
    count = forms.IntegerField(min_value=1, label="Number of recipes")


class SpoonacularImportForm(forms.Form):
    count = forms.IntegerField(min_value=1, label="Number of recipes")

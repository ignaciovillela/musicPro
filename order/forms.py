from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    value = forms.IntegerField(
        disabled=True,
        widget=forms.TextInput(),
    )
    usd_value = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        disabled=True,
        widget=forms.TextInput(),
    )

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city',
                  'currency', 'value', 'usd_value']

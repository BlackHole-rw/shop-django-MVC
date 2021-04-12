from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICE = (
    ('S', 'Stripe'),
    ('P', 'Paypal')
)

class CheckoutForm(forms.Form):
    shipping_address1 = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': "1234 Main St"
    }))
    shipping_address2 = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': "Apartment or suite"
    }))
    shipping_country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'country'
    }))
    shipping_zip = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    use_shipping_address = forms.BooleanField(required=False)
    save_shipping_address = forms.BooleanField(required=False)

    billing_address1 = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': "1234 Main St"
    }))
    billing_address2 = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': "Apartment or suite"
    }))
    billing_country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'country'
    }))
    billing_zip = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    use_billing_address = forms.BooleanField(required=False)
    save_billing_address = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICE)

class PromoCode(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': "form-control",
        'placeholder': "Promo code",
        'aria-label': "Recipient's username",
        'aria-describedby': "basic-addon2"
    }))

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': '4'
    }))
    email = forms.EmailField()
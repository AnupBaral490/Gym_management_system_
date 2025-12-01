from django import forms
from .models import NewsletterSignup, Payment

# from .models import PersonalTrainerApplication  # Removed because it does not exist

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSignup
        fields = ['first_name', 'last_name', 'email', 'message']

class PaymentSubmissionForm(forms.ModelForm):
    transaction_code = forms.CharField(required=False, label="Transaction/Reference Code")

    class Meta:
        model = Payment
        fields = ['payment_screenshot', 'transaction_code']
    
    def clean(self):
        cleaned_data = super().clean()
        screenshot = cleaned_data.get('payment_screenshot')
        code = cleaned_data.get('transaction_code')
        if not screenshot and not code:
            raise forms.ValidationError("Please upload a screenshot or enter a transaction code.")
        return cleaned_data
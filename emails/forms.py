from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError


# Creates a form - EmailTicketForm
class EmailTicketForm(forms.Form):
    # from_email = forms.EmailField(label="From", required=False)  # filled automatically
    
    # Fields from the form
    to_email = forms.CharField(
        label="To",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'email@example.com, another@example.com',
            'class': 'form-control'
        })
    )
    
    cc_email = forms.CharField(
        label="CC",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'email@example.com, another@example.com',
            'class': 'form-control'
        })
    )
    
    bcc_email = forms.CharField(
        label="BCC",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'email@example.com, another@example.com',
            'class': 'form-control'
        })
    )
    
    # subject = forms.CharField(label="Subject", max_length=255, disabled=True)
    attachment = forms.FileField(label="Attachment", required=False)
    
    # Validate the fields
    def clean_to_email(self):
        emails = self.cleaned_data.get('to_email', '')
        return self._validate_emails(emails, required=True)
    
    def clean_cc_email(self):       
        emails = self.cleaned_data.get('cc_email', '')
        return self._validate_emails(emails, required=False)   
    
    def clean_bcc_email(self):
        emails = self.cleaned_data.get('bcc_email', '')
        return self._validate_emails(emails, required=False)
    
     # --------------------------
     # HELPER FUNCTION
     # -------------------------
    
    def _validate_emails(self, emails_string, required=False):
        if not emails_string.strip():
            if required:
                raise forms.ValidationError("This field is mandatory")
            return ''
        
        # Split the emails and remove empty entries
        email_list = [email.strip() for email in emails_string.split(',') if email.strip()]
        
        if required and not email_list:
            raise forms.ValidationError("Enter at least one valid email")
        
        # Validate each email individually
        for email in email_list:
            try:
                validate_email(email)
            except DjangoValidationError:
                raise forms.ValidationError(f"Invalid email: {email}")
        
        return emails_string

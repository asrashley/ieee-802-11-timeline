from django import forms
from django.db.models import fields

class DateModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DateModelForm, self).__init__(*args, **kwargs)
        for f in self.instance._meta.fields:
            if isinstance(f,fields.DateField):
                self.fields[f.name].widget.attrs['class'] = 'vDateField'
            elif isinstance(f,fields.URLField):
                self.fields[f.name].widget.attrs['class'] = 'vURLField'

from django.db.models.base import Model
from django.forms import ModelForm, widgets
from django import forms
from .models import Project, Review
from .models import Enregistrement


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'featured_image', 'description',
                  'demo_link', 'source_link']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

        # self.fields['title'].widget.attrs.update(
        #     {'class': 'input'})

        # self.fields['description'].widget.attrs.update(
        #     {'class': 'input'})
        
class EnregistrementForm(forms.ModelForm):
    class Meta:
        model = Enregistrement
        fields = ['nom', 'prenom', 'email','contenu','etat','avis']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'input'}),
            'prenom': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'contenu': forms.TextInput(attrs={'class': 'input'}),
            'idrec': forms.TextInput(attrs={'class': 'input'}),
            'etat': forms.TextInput(attrs={'class': 'input'}),
            'avis': forms.TextInput(attrs={'class': 'input'}),
            
        }
    def __init__(self, *args, **kwargs):
        super(EnregistrementForm, self).__init__(*args, **kwargs)
        
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ['value', 'body']

        labels = {
            'value': 'Place your vote',
            'body': 'Add a comment with your vote'
        }

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

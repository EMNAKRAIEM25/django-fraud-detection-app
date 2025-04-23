from django.contrib import admin

# Register your models here.
from .models import Project, Review, Tag,Enregistrement

admin.site.register(Project)
admin.site.register(Review)

admin.site.register(Tag)


admin.site.site_header="DevSearch Admin"
admin.site.site_title="DevSearch Admin Panel"


class EnregistrementAdmin(admin.ModelAdmin):
    fields = ('idrec', 'nom', 'prenom', 'email', 'contenu','etat','avis')  
    list_display = ('idrec', 'nom', 'prenom', 'email', 'contenu','etat','avis')
    list_display_links=('nom','prenom')
    list_editable=('contenu','etat','avis',)
    list_filter=('nom','email')
    search_fields=('idrec','nom','prenom')
    
admin.site.register(Enregistrement, EnregistrementAdmin)     
    
    
from django.contrib import admin

# Register your models here.

from .models import Profile, Skill, Message,Formation

admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(Message)



class FormationAdmin(admin.ModelAdmin):
    fields = ('name', 'school', 'difficulty_level', 'rating', 'link','about')  
    list_display = ('name', 'school', 'difficulty_level', 'rating', 'link','about')
    list_display_links=('name','school')
    
    list_filter=('name','rating')
    
    
admin.site.register(Formation, FormationAdmin)     
    
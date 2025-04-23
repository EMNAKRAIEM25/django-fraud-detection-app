from django.core import paginator
from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project, Tag
from .forms import ProjectForm, ReviewForm
from .utils import searchProjects, paginateProjects
from .models import Enregistrement
from .forms import EnregistrementForm
from django.http import JsonResponse

def projects(request):
    

    enregistrements = Enregistrement.objects.all()

    context = {
        'enregistrements': enregistrements
    }
    return render(request, 'projects/projects.html', context)




def save_form(request):
    if request.method == 'POST':
        form = EnregistrementForm(request.POST)
        if form.is_valid():
            enregistrement = form.save(commit=False)
            enregistrement.owner = request.user.profile
            enregistrement.save()
            return redirect('projects')
    else:
        
        form = EnregistrementForm()

    enregistrements = Enregistrement.objects.filter(owner=request.user.profile)

    return render(request, 'projects/projects.html', {'form': form, 'enregistrements': enregistrements})



@login_required(login_url="login")
def update_enregistrement(request, id):
    enregistrement = get_object_or_404(Enregistrement, id=id)

    if request.method == 'POST':
        form = EnregistrementForm(request.POST, instance=enregistrement)
        if form.is_valid():
            form.save()
            return redirect('projects')
    else:
        form = EnregistrementForm(instance=enregistrement, initial={
            'nom': enregistrement.nom,
            'prenom': enregistrement.prenom,
            'email': enregistrement.email,
            'contenu':enregistrement.contenu,
            'idrec':enregistrement.idrec,
            'avis':enregistrement.avis,
            'etat':enregistrement.etat
            
        })

    context = {
        'form': form,
        'enregistrement': enregistrement
    }
    return render(request, 'projects/projectform.html', context)

@login_required(login_url="login")
def delete_enregistrement(request, id):
    enregistrement = get_object_or_404(Enregistrement, id=id)
    
    if request.method == 'POST':
        enregistrement.delete()
        return redirect('projects')
    
    context = {
        'enregistrement': enregistrement
    }
    return render(request, 'delete_template.html', context)




def recommendations():
    pass


def statistics():
    pass




















































def project(request, pk):
    projectObj = Project.objects.get(id=pk)
    form = ReviewForm()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        review = form.save(commit=False)
        review.project = projectObj
        review.owner = request.user.profile
        review.save()

        projectObj.getVoteCount

        messages.success(request, 'Your review was successfully submitted!')
        return redirect('project', pk=projectObj.id)

    return render(request, 'projects/single-project.html', {'project': projectObj, 'form': form})


@login_required(login_url="login")
def createProject(request):
    profile = request.user.profile
    form = ProjectForm()

    if request.method == 'POST':
        newtags = request.POST.get('newtags').replace(',',  " ").split()
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = profile
            project.save()

            for tag in newtags:
                tag, created = Tag.objects.get_or_create(name=tag)
                project.tags.add(tag)
            return redirect('account')

    context = {'form': form}
    return render(request, "projects/project_form.html", context)


@login_required(login_url="login")
def updateProject(request, pk):
    profile = request.user.profile
    project = profile.project_set.get(id=pk)
    form = ProjectForm(instance=project)

    if request.method == 'POST':
        newtags = request.POST.get('newtags').replace(',',  " ").split()

        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save()
            for tag in newtags:
                tag, created = Tag.objects.get_or_create(name=tag)
                project.tags.add(tag)

            return redirect('account')

    context = {'form': form, 'project': project}
    return render(request, "projects/project_form.html", context)


@login_required(login_url="login")
def deleteProject(request, pk):
    profile = request.user.profile
    project = profile.project_set.get(id=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('projects')
    context = {'object': project}
    return render(request, 'delete_template.html', context)

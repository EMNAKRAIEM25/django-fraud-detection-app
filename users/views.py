from django.dispatch.dispatcher import receiver
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import conf
from django.db.models import Q
from .models import Profile, Message
from .forms import CustomUserCreationForm, ProfileForm, SkillForm, MessageForm
from .utils import searchProfiles, paginateProfiles
from django.contrib.auth.decorators import permission_required
import nltk
from nltk.chat.util import Chat, reflections
import os
import pickle


from django.dispatch.dispatcher import receiver
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import conf
from django.db.models import Q
from .models import Profile, Message
from .forms import CustomUserCreationForm, ProfileForm, SkillForm, MessageForm
from .utils import searchProfiles, paginateProfiles
from dash import Dash, html

def loginUser(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('profiles')

    if request.method == 'POST':
        username = request.POST['username'].lower()
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(request.GET['next'] if 'next' in request.GET else 'account')

        else:
            messages.error(request, 'Username OR password is incorrect')

    return render(request, 'users/login_register.html')


def logoutUser(request):
    logout(request)
    messages.info(request, 'User was logged out!')
    return redirect('login')


def registerUser(request):
    page = 'register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            messages.success(request, 'User account was created!')

            login(request, user)
            return redirect('edit-account')

        else:
            messages.success(
                request, 'An error has occurred during registration')

    context = {'page': page, 'form': form}
    return render(request, 'users/login_register.html', context)


def profiles(request):
    profiles, search_query = searchProfiles(request)

    custom_range, profiles = paginateProfiles(request, profiles, 3)
    context = {'profiles': profiles, 'search_query': search_query,
               'custom_range': custom_range}
    return render(request, 'users/profiles.html', context)


def userProfile(request, pk):
    profile = Profile.objects.get(id=pk)

    topSkills = profile.skill_set.exclude(description__exact="")
    otherSkills = profile.skill_set.filter(description="")

    context = {'profile': profile, 'topSkills': topSkills,
               "otherSkills": otherSkills}
    return render(request, 'users/user-profile.html', context)


@login_required(login_url='login')
def userAccount(request):
    profile = request.user.profile

    skills = profile.skill_set.all()
    projects = profile.project_set.all()

    context = {'profile': profile, 'skills': skills}
    return render(request, 'users/account.html', context)


@login_required(login_url='login')
def editAccount(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            return redirect('account')

    context = {'form': form}
    return render(request, 'users/profile_form.html', context)


@login_required(login_url='login')
def createSkill(request):
    profile = request.user.profile
    form = SkillForm()

    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.owner = profile
            skill.save()
            messages.success(request, 'Skill was added successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required(login_url='login')
def updateSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    form = SkillForm(instance=skill)

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill was updated successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required(login_url='login')
def deleteSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill was deleted successfully!')
        return redirect('account')

    context = {'object': skill}
    return render(request, 'delete_template.html', context)


@login_required(login_url='login')
def inbox(request):
    profile = request.user.profile
    messageRequests = profile.messages.all()
    unreadCount = messageRequests.filter(is_read=False).count()
    context = {'messageRequests': messageRequests, 'unreadCount': unreadCount}
    return render(request, 'users/inbox.html', context)


@login_required(login_url='login')
def viewMessage(request, pk):
    profile = request.user.profile
    message = profile.messages.get(id=pk)
    if message.is_read == False:
        message.is_read = True
        message.save()
    context = {'message': message}
    return render(request, 'users/message.html', context)


def createMessage(request, pk):
    recipient = Profile.objects.get(id=pk)
    form = MessageForm()

    try:
        sender = request.user.profile
    except:
        sender = None

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient

            if sender:
                message.name = sender.name
                message.email = sender.email
            message.save()

            messages.success(request, 'Your message was successfully sent!')
            return redirect('user-profile', pk=recipient.id)

    context = {'recipient': recipient, 'form': form}
    return render(request, 'users/message_form.html', context)










def profiles(request):
    profiles, search_query = searchProfiles(request)

    custom_range, profiles = paginateProfiles(request, profiles, 3)
    
    chatbot_rules = [
        ["hello ?", [ "Hi there!"]],
        ["hi", ["Hello!", "Hi there!"]],
        ["how are you ?", ["I'm doing well, thank you!"]],
        ["help ?", ["I can provide assistance with online banking security. How can I help you?"]],
        ["security measures ?", ["Our security measures include multi-factor authentication, encryption, and fraud detection systems."]],
        ["fraud detection ?", ["We employ advanced algorithms and machine learning techniques to detect and prevent fraudulent activities."]],
        ["report fraud ?", ["If you suspect any fraudulent activity, please contact our customer support immediately."]],
        ["password reset ?", ["To reset your password, visit our website and follow the instructions under the 'Forgot Password' section."]],
        ["transaction history ?", ["You can view your transaction history by logging into your online banking account and navigating to the 'Transactions' section."]],
        ["contact information ?", ["You can find our customer support contact information on our website or your account statements."]],
        ["exit", ["Thank you for using our chatbot. Goodbye!"]],
        ["account balance ?", ["To check your account balance, log into your online banking account and go to the 'Account Summary' page."]],
        ["transfer funds ?", ["To transfer funds between your accounts, select the 'Transfer' option in your online banking menu and follow the instructions."]],
        ["mobile banking ?", ["Our mobile banking app is available for download on iOS and Android devices. It provides convenient access to your accounts and various banking services."]],
        ["interest rates ?", ["Our current interest rates can be found on our website or by contacting our customer support."]],
        ["credit card application ?", ["To apply for a credit card, visit our website and fill out the online application form. You will receive a response within a few business days."]],
        ["loan options ?", ["We offer a variety of loan options, including personal loans, home loans, and auto loans. To learn more, visit our website or speak to our loan specialists."]],
        ["ATM locations ?", ["You can find our ATM locations by using our mobile banking app or visiting our website's 'Locations' page."]],
        ["online banking registration ?", ["To register for online banking, visit our website and click on the 'Register' button. Follow the instructions to create your account."]],
        ["account statement ? ", ["You can access your account statements by logging into your online banking account and selecting the 'Statements' option."]],
        ["credit limit increase ?", ["To request a credit limit increase, contact our customer support or visit one of our branch locations."]],
        ["comment sécuriser mon compte en ligne ?", ["Pour sécuriser votre compte en ligne, veuillez suivre ces mesures : utilisez un mot de passe fort et unique, activez l'authentification à deux facteurs, évitez de partager vos informations d'identification et surveillez régulièrement votre compte pour toute activité suspecte."]],
        ["comment mettre à jour mes informations personnelles ?", ["Pour mettre à jour vos informations personnelles, connectez-vous à votre compte en ligne, accédez à la section 'Profil' ou 'Paramètres', puis modifiez les détails nécessaires tels que votre adresse, numéro de téléphone, etc."]],
        ["comment ajouter un bénéficiaire pour les transferts de fonds ?", ["Pour ajouter un bénéficiaire à votre liste de transferts de fonds, connectez-vous à votre compte en ligne, accédez à la section 'Transferts' ou 'Virements', puis suivez les instructions pour ajouter les détails du bénéficiaire."]],
        ["comment annuler un virement ou une transaction ?", ["Pour annuler un virement ou une transaction, contactez notre service clientèle dès que possible. Ils pourront vous guider et vous fournir des instructions spécifiques en fonction de votre situation."]],
        ["quels sont les frais associés à mon compte ?", ["Les frais associés à votre compte peuvent varier en fonction du type de compte que vous avez. Veuillez consulter notre site Web ou contacter notre service clientèle pour obtenir des informations détaillées sur les frais spécifiques à votre compte."]],
        ["comment contester une transaction non autorisée ?", ["Si vous constatez une transaction non autorisée sur votre compte, veuillez contacter immédiatement notre service clientèle pour signaler le problème. Ils vous guideront à travers le processus de contestation et prendront les mesures nécessaires pour résoudre la situation."]],
        ["comment bloquer une carte en cas de perte ou de vol ?", ["En cas de perte ou de vol de votre carte, veuillez contacter notre service clientèle immédiatement pour signaler la situation. Ils pourront bloquer votre carte et vous fournir des instructions pour obtenir une nouvelle carte."]],
        ["Comment ouvrir un compte bancaire ?", ["Pour ouvrir un compte bancaire, vous pouvez vous rendre dans l'une de nos succursales et remplir une demande d'ouverture de compte. Assurez-vous d'avoir les documents nécessaires tels que votre pièce d'identité et une preuve de résidence."]],
        ["Quelles sont les options de paiement disponibles ?", ["Nous offrons plusieurs options de paiement, y compris les virements bancaires, les chèques, les paiements par carte de débit et les paiements en ligne. Vous pouvez choisir la méthode qui vous convient le mieux en fonction de vos besoins."]],
        ["Comment obtenir un prêt hypothécaire ?", ["Pour obtenir un prêt hypothécaire, vous pouvez prendre rendez-vous avec l'un de nos conseillers en prêt hypothécaire. Ils évalueront votre admissibilité, discuteront des options disponibles et vous guideront tout au long du processus de demande."]],
        ["Quels sont les avantages d'une carte de crédit ?", ["Les avantages d'une carte de crédit peuvent inclure des récompenses en points, des remises en argent, une assurance voyage, une protection contre la fraude et la possibilité de construire votre historique de crédit. Les avantages spécifiques peuvent varier en fonction du type de carte que vous choisissez."]],
        ["Comment déposer de l'argent sur mon compte en ligne ?", ["Vous pouvez déposer de l'argent sur votre compte en ligne en utilisant des options telles que les virements bancaires, les dépôts de chèques mobiles ou en effectuant un dépôt en personne dans l'une de nos succursales. Veuillez consulter notre site Web ou contacter notre service clientèle pour obtenir des instructions détaillées."]],
        ["Comment activer une carte de crédit ?", ["Pour activer votre carte de crédit, vous pouvez appeler le numéro de téléphone indiqué sur l'autocollant de la carte ou vous connecter à votre compte en ligne et suivre les instructions fournies pour l'activation de la carte."]],
        ["Quelle est la limite de retrait quotidienne d'un guichet automatique ?", ["La limite de retrait quotidienne d'un guichet automatique dépend du type de compte que vous avez et des politiques de votre banque. Veuillez consulter votre contrat de compte ou contacter notre service clientèle pour connaître les détails spécifiques à votre compte."]],
        ["Comment vérifier le solde d'un compte par téléphone ?", ["Pour vérifier le solde de votre compte par téléphone, vous pouvez appeler notre service automatisé ou parler à l'un de nos représentants du service clientèle. Ils vous guideront à travers le processus de vérification du solde de votre compte."]],
        ["Comment ajouter un nouvel utilisateur au système ?", ["Pour ajouter un nouvel utilisateur au système, suivez ces étapes : 1. Connectez-vous en tant qu'administrateur. 2. Accédez à la section 'Gestion des utilisateurs'. 3. Cliquez sur 'Ajouter un utilisateur' et remplissez les informations requises, telles que le nom, l'adresse e-mail et les autorisations d'accès."]],
        ["Comment réinitialiser le mot de passe d'un utilisateur ?", ["Pour réinitialiser le mot de passe d'un utilisateur, procédez comme suit : 1. Connectez-vous en tant qu'administrateur. 2. Accédez à la section 'Gestion des utilisateurs'. 3. Recherchez l'utilisateur concerné et cliquez sur 'Réinitialiser le mot de passe'. L'utilisateur recevra un e-mail avec les instructions pour définir un nouveau mot de passe."]],
        ["Comment supprimer un utilisateur du système ?", ["Pour supprimer un utilisateur du système, suivez ces étapes : 1. Connectez-vous en tant qu'administrateur. 2. Accédez à la section 'Gestion des utilisateurs'. 3. Recherchez l'utilisateur que vous souhaitez supprimer et cliquez sur 'Supprimer'. Confirmez ensuite la suppression lorsque vous y êtes invité."]],
        ["Comment générer un rapport d'activité du système ?", ["Pour générer un rapport d'activité du système, procédez comme suit : 1. Connectez-vous en tant qu'administrateur. 2. Accédez à la section 'Rapports' ou 'Activité du système'. 3. Sélectionnez les critères de filtrage, tels que la période de temps et les types d'activités, puis cliquez sur 'Générer le rapport'."]],
        ["Comment effectuer une sauvegarde des données du système ?", ["Pour effectuer une sauvegarde des données du système, suivez ces étapes : 1. Connectez-vous en tant qu'administrateur. 2. Accédez à la section 'Sauvegarde' ou 'Gestion des sauvegardes'. 3. Sélectionnez les données que vous souhaitez sauvegarder et choisissez l'emplacement de sauvegarde. Cliquez ensuite sur 'Démarrer la sauvegarde'."]],
        ["Comment configurer les autorisations d'accès pour les utilisateurs ?", ["Pour configurer les autorisations d'accès pour les utilisateurs, suivez ces étapes : 1. Connectez-vous en tant qu'administrateur. 2. Accédez à la section 'Gestion des utilisateurs'. 3. Recherchez l'utilisateur concerné et cliquez sur 'Modifier les autorisations'. Sélectionnez ensuite les autorisations appropriées pour l'utilisateur et enregistrez les modifications."]],
        ["Comment suivre les performances du système ?", ["Pour suivre les performances du système, utilisez des outils de surveillance tels que des tableaux de bord ou des rapports analytiques. Ces outils fournissent des informations sur les temps de réponse, l'utilisation des ressources et d'autres métriques clés pour évaluer les performances globales du système."]],
        ["Comment gérer les problèmes de performance du système ?", ["Pour gérer les problèmes de performance du système, suivez ces étapes : 1. Identifiez les problèmes spécifiques en utilisant des outils de surveillance des performances. 2. Analysez les facteurs qui pourraient influencer les performances, tels que la charge de travail ou les ressources matérielles. 3. Appliquez des correctifs, optimisez les paramètres du système ou envisagez une mise à niveau des ressources si nécessaire."]],
        ["Comment assurer la sécurité des données sensibles ?", ["Pour assurer la sécurité des données sensibles, suivez ces meilleures pratiques : 1. Utilisez des méthodes de cryptage pour protéger les données en transit et au repos. 2. Mettez en œuvre des politiques d'accès et des contrôles d'authentification solides pour limiter l'accès aux données sensibles. 3. Effectuez régulièrement des audits de sécurité pour détecter et corriger les vulnérabilités potentielles."]],
        ["Comment gérer les autorisations d'accès pour les différentes équipes ?", ["Pour gérer les autorisations d'accès pour les différentes équipes, suivez ces étapes : 1. Déterminez les niveaux d'accès requis pour chaque équipe en fonction de leurs responsabilités. 2. Définissez des rôles et des privilèges spécifiques pour chaque équipe. 3. Utilisez des groupes d'utilisateurs ou des profils pour faciliter la gestion des autorisations."]],
        ["Comment planifier des sauvegardes régulières des données ?", ["Pour planifier des sauvegardes régulières des données, suivez ces étapes : 1. Établissez un calendrier de sauvegarde en fonction de la fréquence des modifications des données. 2. Choisissez un emplacement de stockage sécurisé pour les sauvegardes. 3. Utilisez des outils automatisés pour effectuer les sauvegardes à l'heure prévue."]],
        ["Comment surveiller les journaux d'activité du système ?", ["Pour surveiller les journaux d'activité du système, utilisez des outils de journalisation et d'analyse de journaux. Surveillez les activités suspectes, les erreurs et les tendances pour identifier rapidement les problèmes."]],
        ["comment télécharger mes relevés bancaires en format PDF",["Connectez-vous à votre compte en ligne en utilisant vos identifiants. 2. Accédez à la section 'Relevés bancaires' ou 'Documents'. 3. Recherchez l'option qui vous permet de sélectionner la période des relevés que vous souhaitez télécharger. 4. Choisissez la période souhaitée, par exemple, le mois ou le trimestre. 5. Sélectionnez le format de fichier PDF comme option de téléchargement. 6. Cliquez sur le bouton de téléchargement ou sur le lien approprié pour démarrer le téléchargement. 7. Enregistrez le fichier PDF sur votre ordinateur ou périphérique de stockage. Une fois le téléchargement terminé, vous pourrez ouvrir le fichier PDF à l''aide d''un lecteur de PDF tel que Adobe Acrobat Reader pour consulter vos relevés bancaires."]],
        ["Quels sont les avantages de l'authentification à deux facteurs ?", ["L'authentification à deux facteurs offre une couche de sécurité supplémentaire en demandant aux utilisateurs de fournir une deuxième forme d'identification, telle qu'un code généré par une application sur leur téléphone, en plus de leur mot de passe."]],
        ["Comment mettre à jour mes coordonnées bancaires ?", ["Pour mettre à jour vos coordonnées bancaires, veuillez contacter notre service clientèle par téléphone ou visiter l'une de nos succursales. Ils vous guideront à travers le processus de mise à jour de vos informations."]],
        ["Quelles sont les fonctionnalités disponibles dans l'application mobile ?", ["Notre application mobile vous permet de consulter vos soldes de compte, d'effectuer des virements, de payer des factures, de localiser des guichets automatiques et bien plus encore. Téléchargez l'application sur votre appareil mobile pour accéder à toutes ces fonctionnalités."]],
        ["Comment contacter le service clientèle en dehors des heures d'ouverture ?", ["En dehors des heures d'ouverture, vous pouvez nous contacter par e-mail ou utiliser notre service de chat en direct sur notre site web. Nous vous répondrons dès que possible."]],
        ["Puis-je ouvrir un compte bancaire en ligne ?", ["Oui, vous pouvez ouvrir un compte bancaire en ligne en remplissant notre formulaire de demande sur notre site web. Suivez les étapes fournies et fournissez les informations requises pour ouvrir votre compte."]],
        ["Quels sont les types de cartes de crédit que vous proposez ?", ["Nous proposons une gamme de cartes de crédit, y compris des cartes avec des récompenses en points, des cartes de voyage, des cartes de crédit pour les étudiants, et bien d'autres. Choisissez la carte qui correspond le mieux à vos besoins et à vos habitudes de dépenses."]],
        ["Comment vérifier mes relevés de compte en ligne ?", ["Connectez-vous à votre compte en ligne et accédez à la section 'Relevés de compte'. Vous pourrez visualiser, télécharger et imprimer vos relevés de compte dans cette section."]],
        ["Est-ce que vous offrez des services de planification financière ?", ["Oui, nous offrons des services de planification financière pour vous aider à établir des objectifs financiers, à gérer votre budget, à planifier votre retraite et bien plus encore. Prenez rendez-vous avec l'un de nos conseillers financiers pour discuter de vos besoins."]],
        ["Comment mettre à jour ma limite de retrait ?", ["Pour mettre à jour votre limite de retrait, veuillez contacter notre service clientèle par téléphone ou visiter l'une de nos succursales. Nos représentants vous guideront à travers le processus de mise à jour de votre limite."]],
        ["Quelles sont les options de paiement disponibles pour les prêts ?", ["Nous acceptons les paiements par virement bancaire, les chèques, les paiements en ligne et les prélèvements automatiques. Vous pouvez choisir l'option de paiement qui vous convient le mieux en fonction de votre préférence."]],
        ["Comment fonctionne le processus de remboursement d'un prêt ?", ["Le processus de remboursement d'un prêt varie en fonction du type de prêt et des termes spécifiques. En général, vous devrez effectuer des paiements périodiques, mensuels ou hebdomadaires, qui comprennent à la fois le capital emprunté et les intérêts. Vous pouvez effectuer des paiements par virement bancaire, chèque ou prélèvement automatique."]],
        ["Comment demander un prêt personnel ?", ["Pour demander un prêt personnel, vous pouvez remplir une demande en ligne sur notre site web ou vous rendre dans l'une de nos succursales. Vous devrez fournir des informations sur vos revenus, votre historique de crédit et d'autres détails financiers."]],
        ["Quelles sont les conditions pour ouvrir un compte d'épargne ?", ["Les conditions pour ouvrir un compte d'épargne peuvent varier selon la banque, mais généralement, vous devez être majeur, résider dans le pays, fournir une pièce d'identité valide et un justificatif de domicile. Certains comptes d'épargne peuvent avoir un dépôt minimum requis."]],
        ["Comment puis-je annuler un virement que j'ai effectué par erreur ?", ["Si vous avez effectué un virement par erreur, contactez immédiatement notre service clientèle pour signaler la situation. Ils vous fourniront des instructions spécifiques pour annuler ou rectifier le virement."]],
        ["Qu'est-ce qu'un taux d'intérêt nominal ?", ["Un taux d'intérêt nominal est le taux de base annoncé pour un produit financier, tel qu'un compte d'épargne ou un prêt. Cependant, il ne tient pas compte des autres frais ou de l'effet de la capitalisation des intérêts. Le taux d'intérêt nominal est souvent indiqué avant l'application de tout taux promotionnel ou de réduction."]],
        ["Comment puis-je demander un relevé de compte papier ?", ["Pour demander un relevé de compte papier, veuillez contacter notre service clientèle par téléphone ou vous rendre dans l'une de nos succursales. Ils pourront vous aider à obtenir une copie papier de votre relevé de compte."]],
        ["Qu'est-ce qu'un prélèvement automatique ?", ["Un prélèvement automatique est un arrangement qui vous permet de payer automatiquement vos factures ou vos échéances de prêt à partir de votre compte bancaire. Vous devez fournir une autorisation à la partie bénéficiaire pour débiter votre compte selon un calendrier préétabli."]],
        ["Quels sont les systèmes utilisés pour la détection de la fraude ?", ["Nous utilisons des systèmes avancés de détection de la fraude qui combinent des techniques d'apprentissage automatique, d'analyse des modèles et de surveillance des comportements pour détecter les activités suspectes et les schémas de fraude."]],
        ["Comment puis-je signaler une activité suspecte ou une fraude ?", ["Si vous remarquez une activité suspecte ou si vous pensez être victime de fraude, veuillez contacter immédiatement notre service clientèle. Ils vous guideront sur la marche à suivre et prendront les mesures nécessaires pour enquêter sur la situation."]],
        ["Comment puis-je protéger mes informations personnelles contre la fraude en ligne ?", ["Pour protéger vos informations personnelles contre la fraude en ligne, veuillez suivre ces bonnes pratiques : ne partagez pas vos informations sensibles avec des sources non fiables, utilisez des mots de passe forts et uniques, évitez de cliquer sur des liens suspects ou de télécharger des fichiers provenant de sources inconnues, et gardez vos appareils et logiciels à jour."]],
        ["Comment votre banque gère-t-elle les risques liés aux prêts ?", ["Nous avons des politiques et des procédures rigoureuses en place pour évaluer les risques liés aux prêts. Nous effectuons des analyses approfondies des demandes de prêt, y compris l'évaluation de la solvabilité et de la capacité de remboursement des emprunteurs, ainsi que l'examen des garanties proposées."]],
        ["Quelles mesures votre banque prend-elle pour atténuer les risques de fraude en ligne ?", ["Nous utilisons une combinaison de mesures de sécurité pour atténuer les risques de fraude en ligne, notamment l'authentification à deux facteurs, la surveillance des transactions suspectes, la mise en place de protocoles de sécurité avancés, et la sensibilisation continue des clients aux meilleures pratiques de sécurité en ligne."]],
        ["Comment puis-je signaler une vulnérabilité de sécurité ?", ["Si vous découvrez une vulnérabilité de sécurité dans nos systèmes, veuillez la signaler immédiatement à notre équipe de sécurité en contactant notre service clientèle. Nous prenons les questions de sécurité très au sérieux et nous traiterons votre signalement avec la plus grande confidentialité."]],
        ["Quels sont les indicateurs utilisés pour la détection de la fraude ?", ["Nous utilisons une variété d'indicateurs pour détecter la fraude, tels que les schémas de comportement inhabituels, les transactions de montants anormaux, les adresses IP suspectes, les activités de connexion inhabituelles, les tentatives répétées d'accès non autorisé, et les signaux de fraude connus provenant de sources externes."]],
        ["Comment puis-je protéger mes cartes de débit et de crédit contre la fraude ?", ["Pour protéger vos cartes de débit et de crédit contre la fraude, veuillez suivre ces conseils : ne partagez pas vos informations de carte avec des tiers, ne laissez pas votre carte sans surveillance, vérifiez régulièrement vos relevés de compte, signalez immédiatement toute activité suspecte à votre banque, et activez les notifications de transaction sur votre compte."]],
        ["Comment votre banque détecte-t-elle les activités frauduleuses ?", ["Nous utilisons une combinaison de techniques avancées de détection de fraude, y compris l'analyse des modèles, l'apprentissage automatique et l'examen manuel des transactions suspectes. Nous surveillons en permanence les activités de nos clients afin de détecter et de prévenir toute activité frauduleuse."]],
        ["Quelles sont les mesures de sécurité pour protéger les comptes en ligne ?", ["Nous utilisons des mesures de sécurité telles que l'authentification à deux facteurs, le cryptage des données, la surveillance des activités suspectes, et des protocoles de sécurité robustes pour protéger les comptes en ligne de nos clients."]],
        ["Comment puis-je signaler une tentative de phishing ?", ["Si vous recevez un e-mail ou un message suspect vous demandant des informations confidentielles, ne répondez pas et ne cliquez sur aucun lien. Signalez immédiatement l'e-mail ou le message à notre service clientèle afin que nous puissions enquêter sur la tentative de phishing."]],
        ["Quels sont les signes d'une activité frauduleuse sur mon compte ?", ["Certains signes d'une activité frauduleuse peuvent inclure des transactions inconnues ou non autorisées, des modifications inattendues de vos informations de compte, des notifications de connexion suspectes ou des demandes de confirmation d'activités que vous n'avez pas effectuées. Si vous remarquez l'un de ces signes, veuillez contacter notre service clientèle immédiatement."]],
        ["Comment puis-je protéger mes informations de connexion ?", ["Pour protéger vos informations de connexion, veuillez utiliser des mots de passe forts et uniques, éviter de les partager avec d'autres personnes, ne pas les enregistrer sur des appareils publics ou non sécurisés, et mettre à jour régulièrement vos mots de passe."]],
        ["Quelles sont les procédures de vérification pour les transactions suspectes ?", ["Lorsque nous détectons une transaction suspecte, nous effectuons une vérification supplémentaire en contactant le titulaire du compte pour confirmer l'activité. Nous pouvons également bloquer temporairement les fonds ou suspendre les transactions suspectes jusqu'à ce que nous puissions confirmer leur légitimité."]],
        ["Quelles sont les mesures prises pour prévenir la fraude en ligne ?", ["Nous mettons en œuvre des outils de détection de la fraude en temps réel, des systèmes de prévention des intrusions, des protocoles de sécurité avancés, et nous collaborons avec des organismes de sécurité et des réseaux de partage d'informations pour lutter contre la fraude en ligne."]],
        ["Comment votre banque évalue-t-elle les risques liés aux transactions internationales ?", ["Nous utilisons des méthodes d'évaluation des risques pour les transactions internationales, telles que l'analyse des pays de destination, les profils de risque des marchands, les vérifications supplémentaires pour les transactions inhabituelles, et la conformité aux réglementations internationales en matière de lutte contre le blanchiment d'argent et le financement du terrorisme."]],
        ["Comment puis-je signaler un faux site web ou une escroquerie en ligne ?", ["Si vous rencontrez un faux site web ou si vous pensez être victime d'une escroquerie en ligne, veuillez signaler immédiatement l'incident à notre service clientèle. Nous travaillons en étroite collaboration avec les autorités compétentes pour lutter contre la fraude en ligne."]],
        ["Quels sont les mécanismes de sauvegarde des données pour assurer la continuité des opérations en cas d'incident ?", ["Nous avons mis en place des mécanismes de sauvegarde réguliers, des plans de reprise après sinistre et des mesures de continuité des activités pour assurer la protection des données et la continuité des opérations en cas d'incident ou de catastrophe."]],
        ["Comment votre banque gère-t-elle les risques de fraude liés aux cartes de crédit ?", ["Nous avons mis en place un système de gestion des risques de fraude avancé pour les cartes de crédit. Cela comprend la surveillance en temps réel des transactions, l'analyse des modèles de dépenses, la détection des comportements frauduleux et l'utilisation de technologies de pointe pour protéger nos clients contre la fraude financière."]],
        ["Quels sont les signes d'une activité frauduleuse sur ma carte de crédit ?", ["Certains signes d'une activité frauduleuse sur votre carte de crédit peuvent inclure des transactions inconnues ou non autorisées, des facturations incorrectes, des achats répétés à partir de lieux inhabituels, des notifications de connexion suspectes ou des modifications inattendues des limites de crédit. Si vous remarquez l'un de ces signes, veuillez nous contacter immédiatement."]],
        ["Quelles mesures de sécurité sont en place pour protéger ma carte de crédit contre la fraude ?", ["Nous utilisons des mesures de sécurité telles que l'authentification à deux facteurs, la détection des transactions suspectes, la protection par mot de passe, la vérification de l'identité du titulaire de la carte, la technologie de puce EMV et la surveillance continue des activités pour protéger votre carte de crédit contre la fraude."]],
        ["Comment puis-je signaler une transaction frauduleuse sur ma carte de crédit ?", ["Si vous identifiez une transaction frauduleuse sur votre carte de crédit, veuillez nous contacter immédiatement pour signaler le problème. Nous prendrons les mesures nécessaires pour enquêter sur la transaction et protéger votre compte contre toute activité frauduleuse future."]],
        ["Quelles sont les procédures de remboursement en cas de fraude sur ma carte de crédit ?", ["En cas de fraude sur votre carte de crédit, nous avons des procédures de remboursement en place pour vous protéger. Une fois que vous nous avez signalé la fraude, nous enquêterons sur l'incident et, si la fraude est confirmée, nous vous rembourserons les montants frauduleux conformément à nos politiques de remboursement."]],
        ["Comment puis-je protéger ma carte de crédit contre la fraude en ligne ?", ["Pour protéger votre carte de crédit contre la fraude en ligne, veuillez suivre ces conseils : ne partagez jamais vos informations de carte de crédit en ligne sauf avec des sites sécurisés et de confiance, utilisez des mots de passe forts et uniques, évitez de cliquer sur des liens suspects ou douteux, et surveillez régulièrement vos relevés de carte de crédit pour détecter toute activité frauduleuse."]],
        ["Comment puis-je activer ou désactiver les fonctionnalités de sécurité de ma carte de crédit ?", ["Vous pouvez contacter notre service clientèle pour activer ou désactiver certaines fonctionnalités de sécurité de votre carte de crédit, telles que les paiements sans contact, les paiements en ligne ou les paiements à l'étranger. Nous serons heureux de vous aider à personnaliser les paramètres de sécurité de votre carte selon vos préférences."]],
        ["Quelles sont les pratiques recommandées pour protéger ma carte de crédit lors de voyages ?", ["Lors de vos voyages, veuillez prendre les mesures suivantes pour protéger votre carte de crédit : informez votre banque de vos dates et destinations de voyage, évitez d'utiliser des distributeurs automatiques de billets ou des terminaux de paiement non sécurisés, gardez votre carte en sécurité et vérifiez régulièrement vos relevés de carte de crédit pour détecter toute activité suspecte."]],
        ["Comment puis-je mettre en place des alertes de transaction pour ma carte de crédit ?", ["Vous pouvez configurer des alertes de transaction pour votre carte de crédit en vous connectant à votre compte en ligne ou en contactant notre service clientèle. Les alertes peuvent vous informer par SMS, par e-mail ou par notification push des activités de votre carte, vous permettant ainsi de détecter rapidement toute transaction suspecte."]],
        ["Quelles sont les mesures prises pour détecter les cartes de crédit contrefaites ?", ["Nous utilisons des technologies de pointe pour détecter les cartes de crédit contrefaites, y compris la vérification des caractéristiques de sécurité de la carte, l'analyse des modèles d'utilisation, la surveillance des activités frauduleuses connues et la collaboration avec les réseaux d'émetteurs de cartes pour échanger des informations sur les fraudes."]],
        ["Quelles sont les mesures prises pour prévenir la fraude sur les transactions en ligne avec ma carte de crédit ?", ["Nous utilisons des technologies de détection de fraude avancées pour surveiller les transactions en ligne effectuées avec votre carte de crédit. Cela comprend l'analyse des modèles de dépenses, la détection des comportements suspects et l'utilisation de systèmes de sécurité pour protéger vos informations lors des achats en ligne."]],
        ["Comment puis-je mettre en place des alertes de fraude pour ma carte de crédit ?", ["Vous pouvez configurer des alertes de fraude pour votre carte de crédit en vous connectant à votre compte en ligne. Les alertes peuvent vous avertir par SMS, par e-mail ou par notification push en cas d'activité suspecte sur votre carte, vous permettant ainsi de réagir rapidement en cas de fraude potentielle."]],
        ["Quels sont les processus de vérification utilisés lors d'une demande de carte de crédit pour réduire les risques de fraude ?", ["Lors d'une demande de carte de crédit, nous utilisons des processus de vérification rigoureux pour réduire les risques de fraude. Cela peut inclure la vérification des informations personnelles du demandeur, l'évaluation de l'historique de crédit, la confirmation de l'identité du demandeur et la collaboration avec les bureaux de crédit pour vérifier les informations fournies."]],
        ["Comment puis-je signaler un e-mail ou un message suspect prétendant provenir de ma banque ?", ["Si vous recevez un e-mail ou un message suspect prétendant provenir de notre banque, veuillez nous le signaler immédiatement. Ne cliquez pas sur les liens ni ne fournissez d'informations personnelles. Nous enquêterons sur le message et vous fournirons des conseils sur la marche à suivre pour protéger votre compte et signaler les tentatives de fraude."]],
        ["Comment puis-je protéger mes informations de carte de crédit lorsque j'effectue des achats en ligne ?", ["Lorsque vous effectuez des achats en ligne, assurez-vous de vérifier que le site est sécurisé et utilise le protocole HTTPS. Évitez de saisir vos informations de carte de crédit sur des sites non sécurisés ou douteux. Utilisez également des options de paiement sécurisées telles que les services de paiement en ligne pour ajouter une couche de sécurité supplémentaire lors des transactions en ligne."]],
        ["Quelles sont les mesures prises pour protéger mes informations de carte de crédit contre les violations de données ?", ["Nous mettons en place des mesures de sécurité strictes pour protéger vos informations de carte de crédit contre les violations de données. Cela comprend l'utilisation de systèmes de cryptage avancés, la segmentation du réseau, la surveillance proactive des activités suspectes et la conformité aux normes de sécurité des cartes de paiement telles que PCI-DSS."]],
        ["Quels sont les facteurs pris en compte lors de l'évaluation du risque de fraude sur une transaction de carte de crédit ?", ["Lors de l'évaluation du risque de fraude sur une transaction de carte de crédit, nous prenons en compte plusieurs facteurs tels que le montant de la transaction, le lieu géographique, les schémas d'utilisation de la carte, les historiques de transactions et les modèles de dépenses. Ces facteurs nous aident à détecter les transactions suspectes et à prendre les mesures appropriées pour protéger votre compte."]],
        ["Comment puis-je mettre à jour mes informations de contact pour recevoir des alertes de fraude ?", ["Pour mettre à jour vos informations de contact et vous assurer de recevoir des alertes de fraude, veuillez vous connecter à votre compte en ligne ou contacter notre service clientèle. Vous pouvez fournir des numéros de téléphone, des adresses e-mail et d'autres informations de contact actualisées pour recevoir les alertes de fraude en temps opportun."]],
        ["Quelles sont les procédures de surveillance en place pour détecter les activités frauduleuses sur les cartes de crédit ?", ["Nous utilisons des systèmes de surveillance en temps réel pour détecter les activités frauduleuses sur les cartes de crédit. Cela inclut la surveillance des transactions, la détection des comportements suspects, l'analyse des modèles de dépenses et l'utilisation de technologies avancées pour identifier rapidement les activités frauduleuses et prendre les mesures nécessaires."]],
        ["Comment puis-je activer ou désactiver la fonctionnalité de paiement sans contact sur ma carte de crédit ?", ["Pour activer ou désactiver la fonctionnalité de paiement sans contact sur votre carte de crédit, vous pouvez vous connecter à votre compte en ligne ou contacter notre service clientèle. Ils pourront vous guider pour personnaliser les paramètres de votre carte selon vos préférences de sécurité."]],
        ["Quels sont les modèles de fraude les plus courants associés aux cartes de crédit ?", ["Les modèles de fraude les plus courants associés aux cartes de crédit incluent la fraude par carte perdue ou volée, la fraude d'identité, la fraude en ligne, la fraude par skimming de carte et la fraude par contrefaçon de carte. Nous avons mis en place des mesures pour détecter et prévenir ces types de fraudes."]],
        ["Quelles sont les méthodes de prévention de la fraude utilisées pour protéger les titulaires de cartes de crédit ?", ["Nous utilisons plusieurs méthodes de prévention de la fraude, notamment l'analyse comportementale, la détection des schémas de dépenses inhabituels, l'examen manuel des transactions suspectes, la vérification de l'identité du titulaire de la carte et la mise en place de règles de sécurité avancées pour les transactions en ligne."]],
        ["Comment la technologie d'apprentissage automatique est-elle utilisée pour la détection de la fraude sur les cartes de crédit ?", ["Nous utilisons des algorithmes d'apprentissage automatique pour analyser les données de transactions et détecter les modèles de fraude potentiels. Ces algorithmes peuvent apprendre à partir de grands ensembles de données et identifier les anomalies ou les schémas de comportement suspects qui pourraient indiquer une fraude."]],
        ["Quels sont les facteurs pris en compte lors de l'évaluation du risque de fraude sur une transaction en temps réel ?", ["Lors de l'évaluation du risque de fraude sur une transaction en temps réel, nous prenons en compte divers facteurs tels que l'emplacement géographique, le montant de la transaction, le profil de dépenses du titulaire de la carte, les règles de sécurité préétablies et les schémas de comportement inhabituels. Ces facteurs sont évalués en quelques secondes pour décider de l'approbation ou du rejet de la transaction."]],
        ["Quels sont les protocoles de sécurité utilisés pour la transmission des données de carte de crédit lors d'une transaction en ligne ?", ["Nous utilisons des protocoles de sécurité avancés tels que le protocole SSL/TLS (Secure Sockets Layer/Transport Layer Security) pour chiffrer et protéger les données de carte de crédit lors de leur transmission sur Internet. Cela garantit que les informations sensibles sont sécurisées et ne peuvent pas être interceptées par des tiers malveillants."]],
        ["Comment les données de transaction sont-elles analysées pour détecter les schémas de fraude ?", ["Les données de transaction sont analysées à l'aide d'outils d'analyse avancés qui utilisent des modèles statistiques, des algorithmes de détection d'anomalies et des techniques d'apprentissage automatique. Ces outils permettent d'identifier les schémas de fraude potentiels en comparant les transactions avec des modèles préétablis et en détectant les comportements atypiques."]],
        ["Quelles sont les mesures prises pour protéger les informations de carte de crédit stockées dans la base de données ?", ["Les informations de carte de crédit stockées dans notre base de données sont cryptées à l'aide d'algorithmes de chiffrement robustes. Nous avons également mis en place des contrôles d'accès stricts et des mesures de sécurité pour empêcher tout accès non autorisé à ces informations sensibles."]],
        ["Comment pouvez-vous garantir la confidentialité des informations de carte de crédit lors de leur traitement ?", ["Nous utilisons des protocoles de sécurité de pointe pour garantir la confidentialité des informations de carte de crédit lors de leur traitement. Cela inclut l'utilisation de serveurs sécurisés, de connexions chiffrées et de restrictions d'accès aux données sensibles. Nous respectons également les normes de conformité telles que PCI-DSS pour assurer la protection des informations de carte de crédit."]],
        ["Quelles sont les étapes suivies en cas de détection d'une transaction frauduleuse ?", ["En cas de détection d'une transaction frauduleuse, nous prenons immédiatement des mesures pour protéger le titulaire de la carte. Cela peut inclure le blocage de la carte, la notification du titulaire de la carte, la recherche de toute autre activité frauduleuse sur le compte et la collaboration avec les autorités compétentes pour enquêter sur l'incident."]],
        ["Comment puis-je signaler une transaction frauduleuse sur ma carte de crédit ?", ["Si vous constatez une transaction frauduleuse sur votre carte de crédit, veuillez nous contacter immédiatement. Nous vous guiderons sur les mesures à prendre, y compris la suspension de la carte, la contestation de la transaction et la sécurisation de votre compte contre toute activité frauduleuse future."]],
        ["Qu'est-ce que le marché boursier ?", ["Le marché boursier est un endroit où les actions de sociétés publiques sont échangées. Il permet aux investisseurs d'acheter et de vendre des actions, ce qui leur donne la possibilité de participer à la propriété des entreprises et de réaliser des profits en fonction des fluctuations des cours des actions."]],
        ["Qu'est-ce qu'un taux d'intérêt ?", ["Le taux d'intérêt est le pourcentage que les emprunteurs doivent payer en plus du montant initial emprunté. Il est déterminé par divers facteurs tels que la politique monétaire, l'offre et la demande, le risque associé à l'emprunteur et la durée du prêt. Les taux d'intérêt peuvent affecter les coûts d'emprunt, les rendements des investissements et l'économie dans son ensemble."]],
        ["Qu'est-ce que l'investissement en actions ?", ["L'investissement en actions consiste à acheter des actions d'une entreprise dans le but de réaliser un profit. Les investisseurs peuvent gagner de l'argent grâce à l'appréciation du cours des actions ou aux dividendes versés par l'entreprise. Cependant, l'investissement en actions comporte des risques et les cours des actions peuvent fluctuer en fonction de divers facteurs économiques, sectoriels et spécifiques à l'entreprise."]],
        ["Qu'est-ce que l'analyse financière ?", ["L'analyse financière est l'évaluation des informations financières d'une entreprise pour comprendre sa santé financière, sa performance et sa valeur. Elle implique l'examen des états financiers, des ratios financiers, des tendances du marché, des prévisions de revenus et d'autres données pertinentes. L'analyse financière est utilisée par les investisseurs, les analystes et les gestionnaires pour prendre des décisions éclairées sur les investissements, l'allocation des ressources et la gestion financière."]],
        ["Qu'est-ce qu'un fonds commun de placement ?", ["Un fonds commun de placement est un véhicule d'investissement collectif géré par une société de gestion. Il permet aux investisseurs d'acheter des parts du fonds, qui sont ensuite investies dans un portefeuille diversifié d'actifs tels que des actions, des obligations, des liquidités, etc. Les fonds communs de placement offrent aux investisseurs une diversification, une gestion professionnelle et une liquidité, car les parts peuvent généralement être rachetées à tout moment."]],
        ["Qu'est-ce qu'un compte d'épargne ?", ["Un compte d'épargne est un type de compte bancaire conçu pour permettre aux individus de déposer et de faire fructifier leur argent à un taux d'intérêt spécifié. Les comptes d'épargne offrent une sécurité et une accessibilité aux fonds, bien que les taux d'intérêt puissent varier en fonction des politiques de la banque et des conditions du marché. Ils sont couramment utilisés pour économiser de l'argent à court terme ou pour constituer un fonds d'urgence."]],
        ["Qu'est-ce qu'une obligation ?", ["Une obligation est un instrument financier par lequel l'émetteur (généralement une entreprise ou un gouvernement) emprunte de l'argent à l'investisseur. En échange, l'émetteur s'engage à rembourser le montant emprunté à une date future convenue, ainsi qu'à verser des intérêts réguliers pendant la durée de l'obligation. Les obligations sont considérées comme des investissements à revenu fixe et sont souvent utilisées pour générer des flux de trésorerie réguliers et comme moyen de diversification dans un portefeuille d'investissement."]],
        ["Qu'est-ce qu'un indice boursier ?", ["Un indice boursier est une mesure statistique conçue pour suivre et représenter la performance globale d'un groupe spécifique d'actions ou du marché dans son ensemble. Les indices boursiers sont souvent utilisés comme indicateurs de référence pour évaluer les performances des investissements, analyser les tendances du marché et comparer les portefeuilles d'actions. Certains exemples populaires d'indices boursiers sont le S&P 500, le Dow Jones Industrial Average (DJIA) et le Nasdaq Composite."]],
        ["Qu'est-ce qu'un plan de retraite ?", ["Un plan de retraite est un ensemble de mesures et d'investissements financiers mis en place pour assurer des revenus suffisants pendant la retraite. Cela peut inclure des régimes de retraite d'entreprise, des régimes de retraite individuels tels que les comptes de retraite individuels (IRA) ou les régimes de retraite par capitalisation, ainsi que d'autres formes d'épargne et de placement destinées à financer les besoins futurs liés à la retraite."]],
        ["Qu'est-ce qu'une option d'achat (call) ?", ["Une option d'achat (call) est un contrat financier qui donne à son détenteur le droit, mais pas l'obligation, d'acheter un actif sous-jacent (comme des actions) à un prix fixé à l'avance (prix d'exercice) pendant une période donnée. Les options d'achat sont utilisées par les investisseurs pour spéculer sur la hausse des prix de l'actif sous-jacent ou pour se protéger contre une baisse potentielle."]],
        ["Qu'est-ce qu'un fonds d'investissement alternatif ?", ["Un fonds d'investissement alternatif est un type de fonds qui investit dans des actifs non traditionnels tels que les matières premières, l'immobilier, les produits dérivés, les hedge funds, etc. Ces fonds visent à diversifier les portefeuilles d'investissement et à générer des rendements potentiels plus élevés, mais ils peuvent également comporter des niveaux de risque plus élevés que les investissements traditionnels en actions et en obligations."]],
        ["Qu'est-ce que l'effet de levier financier ?", ["L'effet de levier financier se réfère à l'utilisation de dettes ou de capitaux empruntés pour augmenter le rendement potentiel d'un investissement. En utilisant l'effet de levier, les investisseurs peuvent augmenter leurs gains grâce à des investissements plus importants que ce qu'ils peuvent se permettre avec leurs propres capitaux. Cependant, l'effet de levier amplifie également les pertes potentielles, ce qui peut augmenter les risques associés à un investissement."]],
        ["Qu'est-ce que l'analyse des flux de trésorerie ?", ["L'analyse des flux de trésorerie est une méthode utilisée pour évaluer la santé financière d'une entreprise en examinant les entrées et les sorties de trésorerie sur une période donnée. Cela implique de passer en revue les états financiers, de calculer les flux de trésorerie provenant des activités opérationnelles, des activités d'investissement et des activités de financement, et d'analyser les tendances et les ratios de liquidité. L'analyse des flux de trésorerie est essentielle pour évaluer la capacité d'une entreprise à générer des liquidités et à faire face à ses obligations financières."]],
        ["Qu'est-ce que la gestion de portefeuille ?", ["La gestion de portefeuille est le processus de prise de décision et de gestion des investissements d'un individu ou d'une entité. Cela implique la sélection d'actifs, l'allocation d'actifs, la gestion des risques, la surveillance des performances et les ajustements stratégiques pour atteindre les objectifs financiers. Les gestionnaires de portefeuille utilisent diverses stratégies et analyses pour maximiser les rendements et minimiser les risques, en tenant compte des préférences, de l'horizon temporel et des contraintes de l'investisseur."]],
        ["Qu'est-ce que l'indice de performance financière (IPF) ?", ["L'indice de performance financière est un indicateur utilisé pour évaluer la performance d'une entreprise ou d'un investissement. Il est calculé en comparant les résultats financiers actuels avec une référence ou une norme préétablie, telle que les résultats passés, les performances du secteur ou les objectifs de l'entreprise. L'IPF peut inclure des mesures telles que le rendement des actifs, le rendement des capitaux propres, la marge bénéficiaire, le ratio d'endettement, etc."]],
        ["Qu'est-ce que la volatilité du marché ?", ["La volatilité du marché se réfère à la mesure de l'amplitude des fluctuations des prix sur les marchés financiers. Une volatilité élevée indique des mouvements de prix plus importants et plus fréquents, tandis qu'une volatilité faible indique des mouvements de prix plus stables. La volatilité du marché est souvent utilisée pour évaluer les risques associés à un investissement ou à un portefeuille, et elle est étroitement surveillée par les investisseurs et les traders."]],
        ["Qu'est-ce qu'un plan financier personnel ?", ["Un plan financier personnel est un document qui détaille les objectifs financiers d'un individu, ainsi que les stratégies et les mesures nécessaires pour les atteindre. Cela peut inclure des éléments tels que l'établissement d'un budget, l'épargne, l'investissement, la planification de la retraite, la gestion des dettes, les assurances, etc. Un plan financier personnel est essentiel pour organiser ses finances, prendre des décisions éclairées et travailler vers la réalisation de ses objectifs financiers à long terme."]],
        ["Qu'est-ce qu'une société de gestion d'actifs ?", ["Une société de gestion d'actifs est une entreprise spécialisée dans la gestion de portefeuilles d'investissement pour le compte de clients. Ces sociétés offrent des services de gestion d'actifs, de conseil en investissement, de recherche et de suivi des performances. Elles peuvent gérer des portefeuilles d'actions, d'obligations, de fonds communs de placement, de fonds négociés en bourse (ETF), etc. Les sociétés de gestion d'actifs agissent en tant que fiduciaires pour leurs clients, en prenant des décisions d'investissement conformes aux objectifs et aux intérêts des clients."]],
        ["Qu'est-ce que l'arbitrage financier ?", ["L'arbitrage financier est une stratégie d'investissement qui profite des différences de prix entre différents marchés, actifs ou instruments financiers. Les investisseurs utilisent l'arbitrage financier pour réaliser des profits en achetant et en vendant rapidement les mêmes actifs sur différents marchés, en tirant parti des écarts de prix temporaires. Cette stratégie repose sur l'idée que les marchés sont généralement efficients, mais peuvent parfois présenter des inefficiences temporaires qui peuvent être exploitées pour réaliser des gains sans risque."]],
        ["Qu'est-ce que le ratio cours/bénéfice (P/E) ?", ["Le ratio cours/bénéfice (P/E), également connu sous le nom de ratio de capitalisation boursière, est un indicateur utilisé pour évaluer le rapport entre le prix d'une action et les bénéfices par action (BPA) d'une entreprise. Il est calculé en divisant le cours de l'action par le BPA. Le ratio P/E est souvent utilisé pour évaluer la valorisation d'une action et pour comparer les valorisations relatives des entreprises dans un secteur ou un marché donné. Un ratio P/E élevé peut indiquer une valorisation élevVoici quelques autres exemples d'éléments qui parlent du domaine de la finance"]],
        ["Qu'est-ce qu'une stratégie d'allocation d'actifs ?", ["Une stratégie d'allocation d'actifs est un plan d'investissement qui vise à répartir les ressources financières entre différentes classes d'actifs, telles que les actions, les obligations, les liquidités, l'immobilier, etc. L'objectif est de diversifier le portefeuille et d'optimiser le rendement tout en contrôlant les risques. Les stratégies d'allocation d'actifs sont basées sur le profil de risque et les objectifs de l'investisseur."]],
        ["Qu'est-ce qu'un marché financier ?", ["Un marché financier est un lieu virtuel ou physique où les actifs financiers tels que les actions, les obligations, les devises, les matières premières, etc., sont échangés entre les acheteurs et les vendeurs. Les marchés financiers fournissent un cadre réglementé pour la négociation, la fixation des prix et la facilitation des transactions. Ils jouent un rôle essentiel dans l'allocation des ressources financières et la détermination des prix des actifs."]],
        ["Qu'est-ce qu'un compte de courtage ?", ["Un compte de courtage est un compte ouvert auprès d'un courtier ou d'une société de courtage qui permet aux investisseurs d'acheter et de vendre des actifs financiers tels que des actions, des obligations, des fonds communs de placement, des options, etc. Les comptes de courtage offrent une plateforme et des outils pour la négociation d'actifs financiers et la gestion du portefeuille."]],
        ["Qu'est-ce que l'analyse technique ?", ["L'analyse technique est une méthode d'analyse des marchés financiers qui se concentre sur l'étude des graphiques, des tendances historiques des prix, des volumes de négociation et des indicateurs mathématiques pour prédire les mouvements futurs des prix. Les analystes techniques utilisent des outils tels que les moyennes mobiles, les bandes de Bollinger, les oscillateurs, etc., pour identifier les modèles et les signaux d'achat ou de vente. L'analyse technique est utilisée par les traders pour prendre des décisions de négociation à court terme."]],
        ["Qu'est-ce qu'une option de vente (put) ?", ["Une option de vente (put) est un contrat financier qui donne à son détenteur le droit, mais pas l'obligation, de vendre un actif sous-jacent (comme des actions) à un prix fixé à l'avance (prix d'exercice) pendant une période donnée. Les options de vente sont utilisées par les investisseurs pour spéculer sur la baisse des prix de l'actif sous-jacent ou pour se protéger contre une hausse potentielle."]],
        ["Qu'est-ce qu'un fonds négocié en bourse (ETF) ?", ["Un fonds négocié en bourse (ETF) est un fonds d'investissement qui est négocié sur une bourse comme une action. Il représente un panier d'actifs tels que des actions, des obligations, des matières premières, des devises, etc., et permet aux investisseurs d'acheter ou de vendre des parts de ce panier. Les ETF offrent une diversification instantanée, une liquidité élevée et des coûts de transaction généralement inférieurs par rapport à d'autres fonds d'investissement."]],
        ["Qu'est-ce que la gestion des risques financiers ?", ["La gestion des risques financiers est le processus de identification, évaluation et gestion des risques financiers auxquels une entreprise ou un individu est exposé. Cela comprend l'identification des risques potentiels, l'évaluation de leur probabilité et de leur impact, la mise en place de stratégies de réduction des risques et la gestion des conséquences financières. Les risques financiers courants incluent les risques de crédit, de marché, de liquidité, de change, opérationnels, etc."]],
        ["Qu'est-ce que l'indice boursier ?", ["Un indice boursier est un indicateur statistique utilisé pour mesurer les performances globales d'un marché financier ou d'un segment spécifique du marché. Il est calculé en agrégeant les cours des actions ou des titres constituant l'indice et en utilisant une formule spécifique. Les indices boursiers sont utilisés pour suivre les tendances du marché, évaluer la performance des investissements et comparer les performances des entreprises dans un secteur donné."]],
        ["Qu'est-ce qu'une obligation d'État ?", ["Une obligation d'État est une dette émise par un gouvernement national pour financer ses activités et projets. Les obligations d'État sont considérées comme des investissements à faible risque car elles sont généralement garanties par le gouvernement émetteur. Les investisseurs qui achètent des obligations d'État prêtent de l'argent au gouvernement et reçoivent des intérêts périodiques jusqu'à l'échéance de l'obligation, où ils reçoivent le remboursement du montant principal."]],
        ["Qu'est-ce qu'une stratégie de couverture ?", ["Une stratégie de couverture est une technique utilisée par les investisseurs pour réduire ou compenser les risques associés à un investissement. Elle consiste généralement à prendre une position opposée ou complémentaire à celle de l'investissement principal afin de limiter les pertes potentielles en cas de mouvements défavorables du marché. Les stratégies de couverture sont couramment utilisées pour se protéger contre les fluctuations des taux de change, des prix des matières premières ou des actions."]],
        ["Qu'est-ce que l'analyse fondamentale ?", ["L'analyse fondamentale est une méthode d'évaluation des investissements qui se concentre sur l'examen des facteurs intrinsèques d'une entreprise, tels que ses états financiers, ses ratios financiers, ses perspectives de croissance, son modèle d'activité, ses concurrents, etc. L'objectif est de déterminer la valeur intrinsèque d'une action ou d'un titre en évaluant sa capacité à générer des revenus et des bénéfices à long terme. L'analyse fondamentale est utilisée par les investisseurs à long terme pour prendre des décisions d'investissement."]],
        ["Qu'est-ce qu'un contrat à terme ?", ["Un contrat à terme est un accord entre deux parties pour acheter ou vendre un actif sous-jacent à un prix convenu (prix à terme) à une date future spécifiée. Les contrats à terme sont utilisés pour se protéger contre les fluctuations des prix des actifs ou pour spéculer sur ces mouvements de prix. Les contrats à terme sont couramment utilisés pour les matières premières, les devises, les taux d'intérêt, etc."]],
        ["Qu'est-ce que l'efficience des marchés financiers ?", ["L'efficience des marchés financiers fait référence à la capacité des marchés à refléter toutes les informations disponibles et à les incorporer rapidement dans les prix des actifs. Selon l'hypothèse d'efficience des marchés, il est difficile pour les investisseurs de réaliser des rendements anormaux en utilisant des informations publiques, car ces informations sont déjà reflétées dans les prix des actifs. Les différents niveaux d'efficience des marchés sont l'efficience faible, semi-forte et forte, en fonction de la rapidité et de l'intégralité de l'incorporation de l'information."]],
        ["Qu'est-ce que l'analyse des coûts-volumes-profits ?", ["L'analyse des coûts-volumes-profits est une méthode utilisée pour évaluer la relation entre les coûts, les volumes de production/vendus et les profits d'une entreprise. Elle permet de déterminer le seuil de rentabilité (point mort), c'est-à-dire le niveau de vente nécessaire pour couvrir tous les coûts et atteindre un profit nul. L'analyse des coûts-volumes-profits est utilisée pour prendre des décisions relatives aux prix, à la production et à la rentabilité."]],
        ["Qu'est-ce que la gestion du capital de travail ?", ["La gestion du capital de travail fait référence à la gestion des ressources financières à court terme d'une entreprise, notamment les liquidités, les stocks, les créances clients et les dettes à court terme. L'objectif est de maintenir un équilibre entre les actifs et les passifs à court terme pour assurer la liquidité opérationnelle et minimiser les risques financiers. La gestion efficace du capital de travail est essentielle pour assurer le bon fonctionnement et la stabilité financière d'une entreprise."]],
        ["Qu'est-ce que la titrisation ?", ["La titrisation est un processus financier par lequel des actifs tels que des prêts hypothécaires, des créances commerciales ou des prêts à la consommation sont regroupés et transformés en titres négociables sur le marché. Ces titres sont ensuite vendus à des investisseurs, ce qui permet aux prêteurs d'obtenir des liquidités immédiates. La titrisation permet de transférer le risque et de diversifier les portefeuilles d'investissement."]],
        ["Qu'est-ce que la planification successorale ?", ["La planification successorale est le processus de préparation et d'organisation de la transmission des biens et des actifs d'une personne à ses héritiers ou bénéficiaires désignés après son décès. Cela implique la rédaction d'un testament, l'établissement de fiducies, la nomination d'un exécuteur testamentaire et la prise de mesures pour minimiser les impôts et les problèmes juridiques liés à la succession. La planification successorale vise à assurer une transition en douceur et à protéVoici quelques autres exemples d'éléments qui parlent du domaine de la finance : python  "]],
        ["Qu'est-ce que le ratio de solvabilité ?", ["Le ratio de solvabilité est un indicateur financier qui mesure la capacité d'une entreprise à honorer ses obligations financières à long terme. Il est calculé en divisant le total des actifs d'une entreprise par son total des dettes. Un ratio de solvabilité élevé indique que l'entreprise dispose d'une solide assise financière et est en mesure de faire face à ses engagements à long terme."]],
        ["Qu'est-ce qu'un swap de devises ?", ["Un swap de devises est un accord entre deux parties pour échanger des montants équivalents de deux devises différentes à un taux de change convenu, avec un engagement de les rééchanger à une date future spécifiée. Les swaps de devises sont utilisés pour couvrir les risques de change ou pour spéculer sur les fluctuations des taux de change. Ils permettent aux parties impliquées de bénéficier d'une certaine stabilité dans leurs flux de trésorerie et de réduire les risques liés aux fluctuations des taux de change."]],
        ["Qu'est-ce que la finance comportementale ?", ["La finance comportementale est une discipline qui étudie comment les facteurs psychologiques et émotionnels influencent les décisions financières et les marchés financiers. Elle remet en question l'hypothèse traditionnelle selon laquelle les investisseurs sont totalement rationnels et prend en compte les biais cognitifs, les émotions et les comportements irrationnels qui peuvent affecter les décisions d'investissement. La finance comportementale examine comment ces facteurs peuvent entraîner des inefficiences sur les marchés et affecter les rendements des investissements."]],
        ["Qu'est-ce qu'une obligation à taux variable ?", ["Une obligation à taux variable est une obligation dont le taux d'intérêt varie en fonction d'un indice de référence, tel que le taux interbancaire offert (LIBOR). Contrairement aux obligations à taux fixe, les obligations à taux variable offrent une rémunération qui s'ajuste périodiquement en fonction des taux d'intérêt du marché. Cela permet aux émetteurs d'obligations et aux investisseurs de s'adapter aux fluctuations des taux d'intérêt."]],
        ["Qu'est-ce qu'un revenu fixe ?", ["Un revenu fixe est une classe d'actifs qui génère un flux de revenus régulier et prévisible pour l'investisseur. Cela inclut les obligations d'État, les obligations d'entreprise, les obligations municipales et d'autres titres à revenu fixe. Les revenus fixes offrent généralement des paiements d'intérêts réguliers et le remboursement du montant principal à l'échéance. Ils sont considérés comme moins risqués que les actions, mais offrent souvent des rendements plus faibles."]],
        ["Qu'est-ce qu'un plan de retraite ?", ["Un plan de retraite est un plan financier et d'épargne qui vise à accumuler des ressources financières pour la période de retraite d'une personne. Cela peut inclure des régimes de retraite d'entreprise, des régimes de retraite individuels (tels que les comptes de retraite individuels - IRA), des régimes de retraite gouvernementaux, etc. Les plans de retraite permettent aux individus de bénéficier d'un revenu régulier et d'une sécurité financière après leur cessation d'activité professionnelle."]],
        ["Qu'est-ce qu'un actif financier ?", ["Un actif financier est un instrument ou un titre qui a une valeur économique et peut être négocié sur les marchés financiers. Cela inclut les actions, les obligations, les options, les contrats à terme, les fonds communs de placement, les devises, etc. Les actifs financiers permettent aux investisseurs de détenir une participation dans une entreprise, de générer des revenus ou de spéculer sur les mouvements de prix."]],
        ["Qu'est-ce qu'un investissement à revenu variable ?", ["Un investissement à revenu variable est un type d'investissement qui génère un flux de revenus qui peut fluctuer dans le temps. Contrairement aux investissements à revenu fixe, tels que les obligations, les investissements à revenu variable, tels que les actions, ne garantissent pas de paiements d'intérêts réguliers. Les investissements à revenu variable offrent un potentiel de rendements plus élevés, mais ils sont également soumis à plus de volatilité et de risques de perte."]],
        ["Qu'est-ce qu'un indice de référence ?", ["Un indice de référence est un indicateur utilisé pour mesurer et suivre les performances d'un marché, d'un secteur ou d'un portefeuille d'investissement. Il sert de point de comparaison pour évaluer la performance d'un investissement ou d'un gestionnaire de fonds. Les indices de référence courants comprennent le S&P 500, le Dow Jones Industrial Average, l'indice FTSE 100, etc. Les investisseurs utilisent les indices de référence pour évaluer la performance de leurs placements et pour prendre des décisions d'investissement informées."]],
        ["Qu'est-ce qu'une société d'investissement ?", ["Une société d'investissement est une entreprise qui collecte des fonds auprès des investisseurs et les investit dans divers actifs financiers. Les sociétés d'investissement peuvent prendre la forme de fonds communs de placement, de sociétés de gestion d'actifs, de sociétés de capital-risque, etc. Elles offrent aux investisseurs la possibilité de diversifier leurs portefeuilles et de bénéficier de la gestion professionnelle des investissements."]],
        ["Qu'est-ce qu'un marché primaire ?", ["Un marché primaire est un marché financier où les nouvelles émissions d'actions, d'obligations ou d'autres titres sont vendues pour la première fois aux investisseurs. Dans un marché primaire, les émetteurs de titres collectent des capitaux en émettant de nouveaux titres. Les marchés primaires peuvent prendre la forme d'offres publiques initiales (IPO), d'émissions d'obligations d'entreprise, etc."]],
        ["Qu'est-ce qu'une analyse de rentabilité ?", ["L'analyse de rentabilité est un processus d'évaluation de la performance financière d'une entreprise ou d'un projet. Elle vise à déterminer si l'investissement génère des bénéfices suffisants par rapport aux coûts engagés. L'analyse de rentabilité comprend l'examen des états financiers, des ratios financiers, des flux de trésorerie, des marges bénéficiaires et d'autres mesures clés pour évaluer la viabilité économique d'une activité."]],
        ["Qu'est-ce qu'une société de gestion d'actifs ?", ["Une société de gestion d'actifs est une entreprise spécialisée dans la gestion de portefeuilles d'investissement pour le compte de clients. Elle peut gérer des fonds communs de placement, des fonds de pension, des comptes individuels et d'autres types de véhicules d'investissement. Les sociétés de gestion d'actifs analysent les opportunités d'investissement, prennent des décisions de placement, gèrent les risques et fournissent des rapports aux clients."]],
        ["Qu'est-ce que l'allocation d'actifs ?", ["L'allocation d'actifs est une stratégie de gestion de portefeuille qui consiste à répartir les investissements entre différentes classes d'actifs, telles que les actions, les obligations, l'immobilier, les matières premières, etc. L'objectif de l'allocation d'actifs est de diversifier le portefeuille pour réduire les risques et maximiser les rendements potentiels. Elle repose sur l'évaluation du profil de risque de l'investisseur, de ses objectifs financiers et des conditions du marché."]],
        ["Qu'est-ce qu'une obligation convertible ?", ["Une obligation convertible est un type d'obligation qui peut être convertie en actions ordinaires de l'émetteur à un certain prix et pendant une période déterminée. Les obligations convertibles offrent aux investisseurs la possibilité de profiter de l'appréciation potentielle des actions de l'entreprise tout en bénéficiant des revenus réguliers d'une obligation. Elles combinent les caractéristiques des actions et des obligations, offrant ainsi une certaine flexibilité aux investisseurs."]],
        ["Qu'est-ce qu'un marché des changes (Forex) ?", ["Le marché des changes, également appelé Forex (Foreign Exchange), est le marché mondial où les devises sont échangées. C'est le marché financier le plus vaste et le plus liquide au monde. Les participants au marché des changes comprennent les banques, les institutions financières, les entreprises multinationales, les investisseurs individuels, etc. Les transactions sur le Forex impliquent l'achat et la vente de paires de devises, telles que l'euro/dollar américain (EUR/USD) ou la livre sterling/yen japonais (GBP/JPY)."]],
        ["Qu'est-ce que l'effet de levier financier ?", ["L'effet de levier financier se réfère à l'utilisation de l'endettement pour augmenter le rendement potentiel d'un investissement. En utilisant l'effet de levier, les investisseurs peuvent contrôler une plus grande quantité d'actifs avec un montant d'argent plus faible. Cela peut augmenter les rendements, mais également accroître les risques. L'effet de levier financier est couramment utilisé dans les opérations d'achat d'immobilier, de trading sur marge et d'autres formes d'investissement."]],
        ["Qu'est-ce qu'un compte de démonstration en trading ?", ["Un compte de démonstration en trading est un compte fourni par un courtier ou une plateforme de trading qui permet aux traders d'exécuter des transactions sans risquer de l'argent réel. Les comptes de démonstration fournissent une simulation réaliste du trading sur les marchés financiers, permettant aux traders de se familiariser avec la plateforme, de tester des stratégies, de comprendre les mouvements de prix et de développer leurs compétences avant de passer à un compte réel."]],
        ["Qu'est-ce que la valeur nominale ?", ["La valeur nominale, également appelée valeur faciale, est la valeur initiale ou le montant nominal d'un titre financier, tel qu'une action ou une obligation. Elle est généralement indiquée sur le certificat du titre et est utilisée pour calculer les paiements d'intérêts ou de dividendes. La valeur nominale est distincte de la valeur marchande, qui peut varier en fonction de l'offre et de la demande sur les marchés financiers."]],
        ["Qu'est-ce qu'un indice boursier ?", ["Un indice boursier est un indicateur qui mesure la performance globale d'un marché financier ou d'un segment spécifique du marché. Il est calculé en agrégeant les cours des actions constituant l'indice selon une formule spécifique. Les indices boursiers sont utilisés pour évaluer les tendances du marché, comparer les performances des actions et servir de référence pour les investissements. Des exemples d'indices boursiers incluent le S&P 500, le Dow Jones Industrial Average, le NASDAQ Composite, etc."]],
        ["Qu'est-ce qu'une société de capital-risque ?", ["Une société de capital-risque est une entreprise d'investissement qui fournit du capital à des entreprises émergentes et à fort potentiel de croissance. Les sociétés de capital-risque investissent généralement dans des entreprises non cotées en bourse et prennent des participations minoritaires. Elles fournissent également un accompagnement stratégique et opérationnel pour aider les entreprises à se développer et à atteindre leur plein potentiel. Les sociétés de capital-risque jouent un rôle crucial dans le soutien à l'innovation et à l'entrepreneuriat."]],
        ["Qu'est-ce qu'une opération sur titres ?", ["Une opération sur titres, également connue sous le nom d'OST, est une transaction qui implique l'achat, la vente ou l'échange de titres tels que des actions, des obligations, des options, etc. Les opérations sur titres peuvent inclure des opérations d'émission, de rachat, de scission, de fusion, de conversion, etc. Elles sont effectuées par des investisseurs, des entreprises et d'autres entités pour diverses raisons, y compris l'investissement, la levée de fonds, la restructuration, etc."]],
        ["Qu'est-ce que la gestion de patrimoine ?", ["La gestion de patrimoine est un ensemble de services financiers fournis aux individus fortunés et aux familles pour gérer, protéger et faire croître leur patrimoine financier. Elle comprend la planification successorale, la gestion de portefeuille, la fiscalité, la gestion de risques, la planification de la retraite, la philanthropie, etc. La gestion de patrimoine vise à aider les clients à atteindre leurs objectifs financiers à long terme tout en prenant en compte leurs besoins spécifiques et leur tolérance au risque."]],
        ["Qu'est-ce que la diversification de portefeuille ?", ["La diversification de portefeuille est une stratégie d'investissement qui consiste à répartir les fonds entre différentes classes d'actifs, secteurs, régions géographiques, etc. L'objectif est de réduire le risque global en évitant d'avoir une exposition excessive à un seul titre ou à un seul marché. La diversification de portefeuille permet de compenser les pertes éventuelles dans une partie du portefeuille avec les gains dans d'autres parties, et d'améliorer le rendement ajusté au risque."]],
        ["Qu'est-ce qu'un produit dérivé ?", ["Un produit dérivé est un instrument financier dont la valeur dépend de l'évolution d'un actif sous-jacent tel que des actions, des obligations, des devises, des matières premières, etc. Les produits dérivés incluent des options, des contrats à terme, des swaps, des contrats d'échange, etc. Ils sont utilisés pour la spéculation, la couverture des risques, l'arbitrage et d'autres stratégies d'investissement avancées."]],
        ["Qu'est-ce que la gestion passive ?", ["La gestion passive, également connue sous le nom de gestion indicielle, est une stratégie d'investissement qui vise à répliquer la performance d'un indice de référence spécifique, tel que le S&P 500, plutôt que de chercher à surperformer le marché. Les gestionnaires de portefeuille passifs investissent dans des fonds indiciels ou des ETF qui reproduisent l'allocation et les composants de l'indice. La gestion passive offre généralement des frais de gestion plus bas et est souvent utilisée pour obtenir une exposition diversifiée à un marché spécifique."]],
        ["Qu'est-ce qu'une action préférentielle ?", ["Une action préférentielle est un type d'action qui confère à son détenteur certains avantages par rapport aux actionnaires ordinaires. Les actionnaires préférentiels ont généralement droit à un dividende fixe ou prioritaire avant le versement de dividendes aux actionnaires ordinaires. En cas de liquidation de l'entreprise, les actionnaires préférentiels ont également priorité sur les actionnaires ordinaires pour récupérer leur investissement initial. Cependant, les actionnaires préférentiels ont souvent des droits de vote limités ou nuls."]],
        ["Qu'est-ce que l'effet de levier opérationnel ?", ["L'effet de levier opérationnel est une mesure de la sensibilité des bénéfices d'une entreprise aux variations de son chiffre d'affaires. Il mesure la proportion des coûts fixes dans la structure de coûts d'une entreprise. Plus les coûts fixes sont élevés par rapport aux coûts variables, plus l'entreprise aura un effet de levier opérationnel élevé. L'effet de levier opérationnel peut amplifier les bénéfices lorsque les ventes augmentent, mais peut également augmenter les pertes lorsque les ventes diminuent."]],
        ["Qu'est-ce qu'une option d'achat d'actions (stock option) ?", ["Une option d'achat d'actions, également connue sous le nom de stock option, est un contrat qui donne à son titulaire le droit d'acheter des actions de l'entreprise à un prix convenu à l'avance (prix d'exercice) pendant une période déterminée. Les options d'achat d'actions sont souvent accordées aux employés comme incitation ou rémunération supplémentaire. Elles leur permettent d'acheter des actions de l'entreprise à un prix avantageux à l'avenir, en espérant une appréciation de la valeur de ces actions."]],
        ["Qu'est-ce qu'un indice de volatilité ?", ["Un indice de volatilité est un indicateur qui mesure l'anticipation du marché en ce qui concerne la volatilité future des prix des actifs. L'indice de volatilité le plus connu est l'indice VIX (CBOE Volatility Index), qui mesure la volatilité attendue sur le marché des options sur actions. Un indice de volatilité élevé indique généralement une anticipation de mouvements de prix importants ou de périodes d'incertitude sur le marché."]],
        ["Qu'est-ce qu'un actif non liquide ?", ["Un actif non liquide est un actif qui ne peut pas être facilement converti en espèces sans subir une perte de valeur significative ou sans prendre beaucoup de temps. Cela peut inclure des actifs physiques tels que des biens immobiliers, des équipements ou des œuvres d'art, ainsi que des actifs financiers tels que des obligations à long terme ou des participations dans des entreprises non cotées en bourse. Les actifs non liquides peuvent être plus difficiles à vendre rapidement et peuvent nécessiter une période de temps plus longue pour trouver un acheteur approprié."]],
        ["Qu'est-ce que le risque de change ?", ["Le risque de change est le risque que la valeur d'une devise étrangère fluctue par rapport à la devise d'un investisseur ou d'une entreprise. Il peut se produire lorsqu'une entreprise réalise des transactions internationales, détient des actifs ou des passifs dans une devise étrangère ou investit dans des marchés étrangers. Les fluctuations des taux de change peuvent avoir un impact sur les revenus, les coûts, les marges bénéficiaires et la valeur des investissements."]],
        ["Qu'est-ce qu'un ordre de marché ?", ["Un ordre de marché est une instruction donnée à un courtier ou à une plateforme de trading pour acheter ou vendre un actif financier au meilleur prix disponible sur le marché. Lorsqu'un ordre de marché est exécuté, l'opération est effectuée immédiatement au prix en vigueur. Cela garantit une exécution rapide de l'ordre, mais le prix d'exécution peut varier en fonction de la liquidité et des conditions du marché."]],
        ["Qu'est-ce qu'un indice des prix à la consommation (IPC) ?", ["Un indice des prix à la consommation (IPC) est un indicateur statistique qui mesure les variations des prix d'un panier de biens et de services représentatif de la consommation des ménages. L'IPC est utilisé pour mesurer l'inflation et l'évolution du coût de la vie. Il est calculé en comparant les prix des produits et services d'une période à l'autre, en utilisant une année de référence comme base. Les IPC nationaux sont publiés régulièrement par les agences gouvernementales et sont largement suivis par les économistes, les décideurs politiques et les investisseurs."]],
        ["Qu'est-ce que l'analyse technique ?", ["L'analyse technique est une méthode d'évaluation des marchés financiers qui se concentre sur l'étude des données historiques des prix et des volumes de négociation pour prévoir les tendances futures. Les analystes techniques utilisent des graphiques, des indicateurs techniques et des modèles de prix pour identifier les schémas récurrents et prendre des décisions d'achat ou de vente. L'analyse technique est basée sur l'idée que les prix passés peuvent fournir des indications sur les mouvements futurs des prix."]],
        ["Qu'est-ce qu'une offre publique initiale (IPO) ?", ["Une offre publique initiale (IPO) est le processus par lequel une entreprise devient publique en émettant des actions pour la première fois sur un marché boursier. L'IPO permet à l'entreprise de lever des capitaux auprès d'investisseurs publics et de devenir cotée en bourse. Pendant l'IPO, des actions sont vendues aux investisseurs et l'entreprise fait ses débuts sur le marché public. L'IPO est souvent utilisée pour financer la croissance de l'entreprise, offrir des liquidités aux actionnaires existants ou permettre une sortie pour les investisseurs préexistants."]],
        ["Qu'est-ce qu'un taux d'intérêt nominal ?", ["Un taux d'intérêt nominal est le taux d'intérêt déclaré sur un prêt, une obligation ou un compte d'épargne, sans tenir compte de l'inflation ou d'autres facteurs. Il représente le coût ou le rendement de l'argent sans ajustement pour les variations du pouvoir d'achat de la monnaie au fil du temps. Le taux d'intérêt nominal peut différer du taux d'intérêt réel, qui tient compte de l'inflation et reflète le rendement réel ajusté pour l'inflation."]],
        ["Qu'est-ce que la planification financière ?", ["La planification financière est le processus de gestion et de gestion des ressources financières pour atteindre les objectifs financiers d'un individu, d'une famille ou d'une entreprise. Cela implique l'identification des objectifs financiers, l'évaluation de la situation financière actuelle, l'élaboration de stratégies pour atteindre ces objectifs, la mise en œuvre de ces stratégies et le suivi régulier de la situation financière. La planification financière peut inclure des aspects tels que la budgétisation, l'investissement, la planification de la retraite, la planification successorale, etc."]],
        ["Qu'est-ce qu'une obligation à coupon zéro ?", ["Une obligation à coupon zéro est une obligation qui ne verse pas d'intérêts périodiques pendant sa durée de vie. Au lieu de cela, l'obligation est vendue à un prix inférieur à sa valeur nominale et le détenteur reçoit le paiement intégral de la valeur nominale à l'échéance. La différence entre le prix d'achat et la valeur nominale représente le rendement de l'obligation. Les obligations à coupon zéro sont souvent utilisées dans la planification successorale ou pour des objectifs de financement spécifiques."]],
        ["Qu'est-ce que la création monétaire ?", ["La création monétaire est le processus par lequel la monnaie est produite et introduite dans l'économie. Elle peut se produire de différentes manières, notamment par le biais de la banque centrale qui crée de la monnaie fiduciaire (billets de banque) ou par le biais du système bancaire commercial qui crée de la monnaie scripturale (dépôts bancaires). La création monétaire a un impact sur l'offre de monnaie, l'inflation, les taux d'intérêt et d'autres aspects de l'économie."]],
       
       
        ["Qu'est-ce que le trading sur marge ?", ["Le trading sur marge est une pratique d'investissement qui permet aux investisseurs d'emprunter des fonds pour acheter des actifs financiers. L'investisseur dépose un montant initial, appelé marge, auprès d'un courtier, qui lui prête ensuite des fonds supplémentaires pour augmenter son pouvoir d'achat. Le trading sur marge amplifie les gains potentiels, mais expose également les investisseurs à des pertes plus importantes. Il est souvent utilisé par les traders actifs pour tirer parti des fluctuations des prix à court terme."]],
        ["Qu'est-ce que la valeur temps ?", ["La valeur temps est une composante du prix d'une option. Elle représente la valeur que les acheteurs d'options sont prêts à payer pour la possibilité de bénéficier de mouvements futurs des prix de l'actif sous-jacent avant l'échéance de l'option. La valeur temps diminue à mesure que l'échéance de l'option approche, car il reste moins de temps pour que l'option se valorise. Elle est influencée par des facteurs tels que la volatilité, les taux d'intérêt et les dividendes."]],
        ["Qu'est-ce qu'une fusion-acquisition ?", ["Une fusion-acquisition est une opération dans laquelle deux entreprises décident de fusionner leurs activités ou dans laquelle une entreprise acquiert une autre entreprise. Les fusions-acquisitions sont souvent réalisées dans le but d'atteindre des synergies, de renforcer la position sur le marché, d'élargir les activités ou de réaliser des économies d'échelle. Ces opérations peuvent être réalisées en échange d'argent, d'actions ou d'une combinaison des deux."]],
        ["Qu'est-ce qu'un prêt hypothécaire ?", ["Un prêt hypothécaire est un prêt accordé par un prêteur, tel qu'une banque, à un emprunteur pour l'achat d'un bien immobilier. Le bien immobilier est utilisé comme garantie pour le prêt, ce qui signifie que si l'emprunteur ne rembourse pas le prêt conformément aux modalités convenues, le prêteur peut saisir le bien immobilier pour récupérer le montant du prêt. Les prêts hypothécaires sont généralement remboursés sur une période de plusieurs années avec des intérêts."]],
        ["Qu'est-ce que l'indice de confiance des consommateurs ?", ["L'indice de confiance des consommateurs est un indicateur économique qui mesure le degré de confiance des consommateurs dans l'économie et leurs perspectives financières. Il est généralement basé sur des enquêtes menées auprès des ménages pour évaluer leurs attitudes et leurs intentions d'achat. L'indice de confiance des consommateurs est utilisé pour évaluer le climat économique, prédire les dépenses des consommateurs et évaluer les perspectives de croissance économique."]],
        ["Qu'est-ce que la fiscalité des entreprises ?", ["La fiscalité des entreprises fait référence aux impôts et aux réglementations fiscales qui s'appliquent aux entreprises. Cela comprend les impôts sur les bénéfices des sociétés, les impôts sur les revenus des entreprises, les taxes sur la valeur ajoutée (TVA), les droits de douane, les taxes foncières et d'autres taxes et obligations fiscales. La fiscalité des entreprises peut varier d'un pays à l'autre et peut avoir un impact significatif sur les résultats financiers et les décisions d'investissement des entreprises."]],
       
        ["Qu'est-ce qu'une banque d'investissement ?", ["Une banque d'investissement est une institution financière qui fournit des services de conseil et d'intermédiation dans les transactions financières pour les entreprises, les gouvernements et les particuliers. Les banques d'investissement sont impliquées dans des activités telles que la souscription d'actions et d'obligations, les fusions et acquisitions, le conseil en gestion, la recherche sur les marchés financiers, la négociation de titres, le financement de projets et d'autres services liés aux investissements."]],
        ["Qu'est-ce qu'un indice boursier ?", ["Un indice boursier est un indicateur qui mesure la performance globale d'un marché financier ou d'un segment spécifique du marché. Il est calculé en agrégeant les cours des actions constituant l'indice selon une méthodologie spécifique. Les indices boursiers sont utilisés pour évaluer les tendances du marché, comparer la performance des actions et servir de référence pour les investissements. Des exemples d'indices boursiers sont le S&P 500, le Dow Jones Industrial Average, le FTSE 100, etc."]],
        ["Qu'est-ce qu'une obligation convertie en actions ?", ["Une obligation convertie en actions est une obligation qui peut être convertie en actions de l'émetteur à un certain prix et pendant une période déterminée. L'obligation convertible offre à son détenteur la possibilité de bénéficier de l'appréciation potentielle des actions de l'entreprise tout en bénéficiant des revenus réguliers de l'obligation. Cela combine les caractéristiques d'une obligation et d'une action, offrant ainsi une certaine flexibilité aux investisseurs."]],
        ["Qu'est-ce que l'évaluation d'entreprise ?", ["L'évaluation d'entreprise est le processus d'estimation de la valeur financière globale d'une entreprise. Cela peut être fait en utilisant différentes méthodes, telles que l'analyse des flux de trésorerie actualisés (DCF), l'évaluation comparative, l'évaluation basée sur les bénéfices, l'évaluation basée sur les actifs, etc. L'évaluation d'entreprise est utilisée dans le cadre de transactions d'achat, de vente ou de fusion-acquisition d'entreprises, ainsi que dans la gestion de portefeuille et d'autres décisions d'investissement."]],
        ["Qu'est-ce que la gestion de trésorerie ?", ["La gestion de trésorerie est le processus de gestion des liquidités d'une entreprise, y compris la collecte, la gestion, l'investissement et l'utilisation des fonds disponibles. Cela comprend la gestion des flux de trésorerie, la gestion des comptes bancaires, la prévision des besoins de trésorerie, la gestion des risques de change et d'intérêt, et la prise de décisions concernant l'investissement et le financement à court terme. La gestion de trésorerie vise à maintenir la liquidité de l'entreprise tout en maximisant la rentabilité et en minimisant les risques."]],
        ["Qu'est-ce qu'une société anonyme (SA) ?", ["Une société anonyme (SA) est une forme juridique d'entreprise qui est détenue par des actionnaires et dont le capital social est divisé en actions. Les actionnaires ne sont généralement pas personnellement responsables des dettes de la société au-delà de leur investissement initial. Les sociétés anonymes sont couramment utilisées pour les grandes entreprises et sont régies par des lois spécifiques qui régissent leur structure, leur gouvernance et leurs obligations légales."]],
       
        
        
      
    
    ]
    
    
    
    
    
    
    chatbot = Chat(chatbot_rules, reflections)

    if request.method == 'POST':
        user_input = request.POST['user_input']
        if user_input:
            response = chatbot.respond(user_input)
            if not response:
                response = "Sorry, I don't have the answer. I will contact an expert and get you the answer. Thank you."
        else:
            response = "Please select an option."
    else:
        user_input = ''
        response = ''

    context = {
        'profiles': profiles,
        'search_query': search_query,
        'custom_range': custom_range,
        'user_input': user_input,
        'response': response,
    }
    return render(request, 'users/profiles.html', context)



from django.shortcuts import render
import os
import plotly.express as px
#def Statistics(request):
    #return render(request, 'Statistics.html')
from users.models import Formation

from django.db.models import Count
from projects.models import Enregistrement

def Statistics(request):
    Formation_objects = Formation.objects.all()
    #fig = px.line(
        #x=[f.difficulty_level for f in Formation_objects],
        #y=[f.rating for f in Formation_objects],
        #title="Formation",
        #labels={'x' : 'Rating', 'y' : 'Difficulty Level'}
        
    #)
    #fig.update_layout(title={
        #'font_size': 22,
        #'xanchor': 'center',
        #'x': 0.5
    #}
    #)
        
    from django.db.models import Sum, F, ExpressionWrapper, FloatField
    total_formations = Formation.objects.count()
   
    # Calculate the count of formations for each unique rating value
    rating_counts = Formation.objects.values('rating').annotate(
    count=Count('rating'),
    percentage=ExpressionWrapper(Count('rating') * 100.0 / total_formations, output_field=FloatField())
)

# Convert the result to a DataFrame
    rating_counts_df = pd.DataFrame(rating_counts)
    
    # Create the pie chart
    
    custom_colors = {
    '4,6': 'lightcyan',
    '4,4': 'deepskyblue',
    'nan': 'darkblue',  # Set the color of "nan" value to darkblue
    '4,7': 'cyan',
    '4,5': 'cyan',
    '4,3': 'steelblue',
    '4,8': 'blue',
    '4,2': 'powderblue'
}
    fig_pie = px.pie(rating_counts_df, names='rating', values='percentage', color_discrete_map=custom_colors)
   # Define custom colors for the pie chart slices (if needed)
    # Define custom colors for the pie chart slices (if needed)
    colors = ['darkblue', 'cyan', 'lightcyan', 'deepskyblue', 'blue', 'royalblue', 'steelblue', 'powderblue']

    # Apply the custom colors and other properties to the pie chart
    fig_pie.update_traces(
        hoverinfo='label+percent',
        textinfo='value',  # Display both label and percentage
        texttemplate='%{value:.1f}%',  # Customize the text display
        textfont_size=14,
        marker=dict(colors=colors, line=dict(color='#000000', width=2)),
        
        
        
    )
    fig_pie.update_layout(
        width=500,  # Adjust the width as needed
        title={'text': "Formation Ratings Percentages"}, # Titre du graphique
        title_x=0.3,  # Centre le titre horizontalement
        title_font_size=20  # Ajuste la taille de la police du titre
        
        
    )
    
    # Filter Enregistrement objects for the current user
    enregistrements = Enregistrement.objects.filter(owner=request.user.profile)
    # Calculate the count of records for each unique value of the 'etat' field
    etat_counts = enregistrements.values('etat').annotate(count=Count('etat'))
    print(etat_counts)

    # Create the pie chart
    custom_colors = {'En attente': 'darkblue', 'traité': 'royalblue', 'En cours': 'cyan', 'Etat 4': 'lightcyan'}
    fig_pie1 = px.pie(etat_counts, names='etat', values='count', color_discrete_map=custom_colors)
    
    # Define custom colors for the pie chart slices
    colors = ['darkblue', 'royalblue', 'cyan', 'lightcyan']
    
    # Apply the custom colors and other properties to the pie chart
    fig_pie1.update_traces(
        hoverinfo='label+percent',
        textinfo='value',
        textfont_size=22,
        marker=dict(colors=colors, line=dict(color='#000000', width=2)),
        
        
        
    )
    fig_pie1.update_layout(
        width=500,  # Adjust the width as needed
        title={'text': "Reclamations Status"}, # Titre du graphique
        title_x=0.3,  # Centre le titre horizontalement
        title_font_size=20  # Ajuste la taille de la police du titre
        
    ) 
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
     # Fetch data from the Formation model
    Formation_objects = Formation.objects.all()

    # Calculate the count of formations for each unique difficulty_level value
    difficulty_level_counts = Formation_objects.values('difficulty_level').annotate(count=Count('difficulty_level'))

    # Create the pie chart
    irises_colors = ['rgb(25, 101, 233)', 'rgb(20, 93, 191)', 'rgb(14, 67, 146)', 'rgb(10, 47, 103)', 'rgb(6, 27, 60)']
    fig_pie2 = px.pie(
        names=[difficulty_level_count['difficulty_level'] for difficulty_level_count in difficulty_level_counts],
        values=[difficulty_level_count['count'] for difficulty_level_count in difficulty_level_counts],
        title="Formation Difficulty Levels",
        color_discrete_sequence=irises_colors)
    # Apply the custom colors and other properties to the pie chart
    fig_pie2.update_traces(
        hoverinfo='label+percent',
        textinfo='value',
        textfont_size=20,
        marker=dict(colors=irises_colors, line=dict(color='#000000', width=2)),
        
    )

    fig_pie2.update_layout(
        width=500,
        title_x=0.3,  # Centre le titre horizontalement
        title_font_size=20,  # Ajuste la taille de la police du titre# Adjust the width as needed
        title={'text': "Formation Difficulty Levels"},
    )
    
    # Récupérer toutes les formations depuis le modèle Django
    Formation_objects = Formation.objects.all()

    df = pd.DataFrame(list(Formation_objects.values()))


    # Créer la table HTML
    table_html = '<table class="table">'
    table_html += '<thead><tr>'
    # Ajouter les en-têtes des colonnes du tableau
    table_html += '<th>ID</th>'
    table_html += '<th>Name</th>'
    table_html += '<th>School</th>'
    table_html += '<th>Difficulty Level</th>'
    table_html += '<th>Rating</th>'
    table_html += '<th>Link</th>'
    table_html += '<th>About</th>'
    table_html += '</tr></thead>'
    table_html += '<tbody>'
    # Ajouter les lignes de données à partir des formations
    for formation in Formation_objects:
        table_html += '<tr>'
        table_html += f'<td>{formation.id}</td>'
        table_html += f'<td>{formation.name}</td>'
        table_html += f'<td>{formation.school}</td>'
        table_html += f'<td>{formation.difficulty_level}</td>'
        table_html += f'<td>{formation.rating}</td>'
        table_html += f'<td>{formation.link}</td>'
        table_html += f'<td>{formation.about}</td>'
        table_html += '</tr>'
    table_html += '</tbody></table>'
    
    
    # Récupérer toutes les profils depuis le modèle Django
    profile_objects = Profile.objects.all()
    df = pd.DataFrame(list(profile_objects.values()))

    # Créer la table HTML
    table_html1 = '<table class="table">'
    table_html1 += '<thead><tr>'
    # Ajouter les en-têtes des colonnes du tableau
    table_html1 += '<th>ID</th>'
    table_html1 += '<th>Name</th>'
    table_html1 += '<th>Email</th>'
    table_html1 += '<th>Username</th>'
    table_html1 += '<th>Social Twitter</th>'
    table_html1 += '<th>Social Linkedin</th>'
    table_html1 += '</tr></thead>'
    table_html1 += '<tbody>'
    # Ajouter les lignes de données à partir des profils
    for profile in profile_objects:
        table_html1 += '<tr>'
        table_html1 += f'<td>{profile.id}</td>'
        table_html1 += f'<td>{profile.name}</td>'
        table_html1 += f'<td>{profile.email}</td>'
        table_html1 += f'<td>{profile.username}</td>'
        table_html1 += f'<td>{profile.social_twitter}</td>'
        table_html1 += f'<td>{profile.social_linkedin}</td>'
        table_html1 += '</tr>'
    table_html1 += '</tbody></table>'
    
    
    
    from users.models import fraudTrain
    fraud_data = fraudTrain.objects.filter(is_fraud=True)

    # Calculer le nombre de fraudes pour chaque genre (homme et femme)
    fraud_by_gender = fraud_data.values('gender').annotate(fraud_count=Count('gender'))

    # Créer le bar chart
    figure = px.bar(fraud_by_gender, x='gender', y='fraud_count', color='gender',
                 labels={'fraud_count': 'Number of Fraudes', 'gender': 'Gender'},
                 title='Number of Fraudes per Gender',
                 color_discrete_sequence=['cyan', 'darkblue'])

    # Mettre à jour la mise en page du graphique
    figure.update_layout(
    xaxis_title='Gender',
    yaxis_title='Number of fraudes',
    title_font_size=20,
    grid=dict(rows=1, columns=2),
    
)
    

    # Convertir le graphique en JSON pour l'envoyer au template
    chart_json = figure.to_json()
    
    category_data = fraudTrain.objects.all()

    # Calculer le nombre d'occurrences de chaque catégorie
    category_counts = category_data.values('category').annotate(count=Count('category'))

    # Créer le bar chart
    figure1 = px.bar(category_counts, x='category', y='count',
                 labels={'count': 'Number of Occurrences', 'category': 'Category'},
                 title='Number Of Occurrences per Category',
                 color_discrete_sequence=['#660099'])

    # Mettre à jour la mise en page du graphique
    figure1.update_layout(
        xaxis_title='Category',
        yaxis_title='Number Of Occurrences',
        title_font_size=20,
        grid=dict(rows=1, columns=2),
        
        
    )
    
    # Convertir le graphique en JSON pour l'envoyer au template
    chart_json1 = figure1.to_json()
    
    
    

    
    # Données pour le pie chart
    labels = ['Fraud', 'Non Fraud']
    values = [len(fraud_data), len(fraudTrain.objects.filter(is_fraud=False))]
    colors = ['#B546FB', '#800bc7']

    # Créer le pie chart
    fig_pie9 = px.pie(names=labels, values=values, color_discrete_sequence=colors)

    # Ajouter l'animation
    fig_pie9.update_traces(
    pull=[0.1, 0],  # Pour séparer légèrement les deux sections
    textinfo='percent+label',
    textfont_size=20,
    marker=dict(line=dict(color='#ffffff', width=2))
)

    # Mettre à jour la mise en page du graphique
    fig_pie9.update_layout(
    title="Fraud vs Non Fraud",
    title_font_size=20,
)

    # Convertir le graphique en JSON pour l'envoyer au template
    chart_json_pie = fig_pie9.to_json()
    
    
    from django.db.models.functions import TruncDate 
    fraud_data = fraudTrain.objects.filter(is_fraud=True)

    # Group fraud cases by date and calculate the count for each date
    fraud_by_date = fraud_data.annotate(date=TruncDate('trans_date_trans_time')).values('date').annotate(count=Count('id'))

    # Prepare data in a format suitable for Plotly line chart
    dates = [data['date'] for data in fraud_by_date]
    counts = [data['count'] for data in fraud_by_date]

   # Create the line chart using Plotly
    fig_line = go.Figure(data=go.Scatter(x=dates, y=counts, mode='lines+markers'))
    # Update the layout to set the title font style
    fig_line.update_layout(
    title_text='Fraud Cases Trend Over Time',
    title_font=dict(family='Arial', size=24, color='black'),  # Customize font family, size, and color
    xaxis_title='Date',
    yaxis_title='Number of Fraud Cases',
    font=dict(family='Arial', size=14, color='black'),  # Customize other font styles in the chart
)


    # Convert the chart to JSON format to send it to the template
    line_chart_json = fig_line.to_json()


    
    
    
    chart_pie1 = fig_pie1.to_html()
    chart_pie2 = fig_pie2.to_html()
    chart_pie = fig_pie.to_html()
    
    
    context = { "table_html": table_html, "table_html1": table_html1 ,  "chart_pie": chart_pie, "chart_pie1": chart_pie1,"chart_pie2": chart_pie2,"chart_json": chart_json,"chart_json1": chart_json1,"chart_json_pie":chart_json_pie,"line_chart":line_chart_json}
    return render(request, 'Statistics.html', context)

#def recommendations(request):
    #return render(request, 'recommendations.html')

import joblib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(sender_email, sender_password, recipient_email, subject, transaction_num, account_num, message):
    # Set up the SMTP server
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # Replace with the appropriate SMTP server port

    try:
        # Create a multipart message and set the headers
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Create the message body
        body = message

        # Add body to the email
        msg.attach(MIMEText(body, "html"))

        # Create a secure connection with the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("An error occurred while sending the email:", str(e)) 
        
def generate_recommendation(transaction_num, account_num):
    recommendation = "The Transaction with Number: {}\n".format(transaction_num)
    recommendation += "associated with the account  Number: {}\n".format(account_num)
    recommendation += "will be blocked.\n"
    recommendation += "The credit card password must change."
    
    return recommendation

def block_account(account_num, test):
    # Recherche du compte dans la DataFrame
    account_index = test[test['cc_num'] == account_num].index
    
    if len(account_index) > 0:
        # Mettre à jour l'état de blocage du compte
        test.loc[account_index, 'is_blocked'] = True
        
        print("Le compte {} a été bloqué avec succès.".format(account_num))
    else:
        print("Le compte est déja bloqué pour suspision de fraude  {}.".format(account_num))
        

from imblearn.under_sampling import RandomUnderSampler
from imblearn.under_sampling import NearMiss
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from IPython.display import HTML
from sklearn.preprocessing import OrdinalEncoder   
from keras.models import load_model
import pandas as pd



def search(request):
    if request.method == 'POST':
        # Reading the training and testing datasets
        train = pd.read_csv(r'C:\Users\Admin\Downloads\Django-2021-master\fraudTrain.csv')
        test = pd.read_csv(r'C:\Users\Admin\Downloads\Django-2021-master\fraudTest.csv')  
        # Creating dependent and independent features dataset
        # Combining the train and test datasets for data cleaning and data visulization
        data = pd.concat([train, test], axis = 0)
        data.head()
        data.reset_index(inplace = True)
        data = data.drop(['index', 'Unnamed: 0'], axis = 1)
        X = data.drop(['is_fraud'], axis = 1)
        Y = data['is_fraud']
        # Encoding the categorical columns
    
        cols = ['trans_date_trans_time', 'merchant', 'category', 'first', 'last',
        'gender', 'street', 'city', 'state', 'job', 'dob', 'trans_num']
        encoder = OrdinalEncoder()
        X[cols] = encoder.fit_transform(X[cols])
        # Scaling
    
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)
        nm_sampler = NearMiss()
        x_sampled, y_sampled = nm_sampler.fit_resample(X, Y)

        print('Data   : ', x_sampled.shape)
        print('Labels : ', y_sampled.shape)
        # Splitting the  sampled datasets into training and testing sets

        x_train, x_test, y_train, y_test = train_test_split(x_sampled, y_sampled, test_size = 0.2, random_state = 2)

        print('Training Data Shape   : ', x_train.shape)
        print('Training Labels Shape : ', y_train.shape)
        print('Testing Data Shape    : ', x_test.shape)
        print('Testing Labels Shape  : ', y_test.shape)
    
   

    
    
 
        
        modele_charge1 = joblib.load(r'C:\Users\Admin\Downloads\Django-2021-master\users\templates\users\model.h5')
       
    
        
        probabilities1 = modele_charge1.predict(x_test)
       
        

  
    
        # Définir un seuil de probabilité de fraude
        seuil_risque = 0.5

        # Example usage
        sender_email = "recycle.tunisia@gmail.com"
        sender_password = "ztntffukvpwraygm"
        recipient_email = "emna99krayem@gmail.com"
        subject = "Fraud Detection"

        # Parcourir les probabilités prédites et attribuer le niveau de risque
        risque_email_envoye = False  # Variable pour suivre l'état de l'envoi d'e-mail
        risques = []
        recommendations = []  # Liste pour stocker les recommandations
    
    
        
        for i, proba in enumerate(probabilities1):    
            if i < len(test):
                transaction_num = str(test.iloc[i]['trans_num'])  # Accéder à la colonne 'trans_num' pour le numéro de transaction
                account_num = str(test.iloc[i]['cc_num'])  # Accéder à la colonne 'cc_num' pour le numéro de compte

                transaction_risk = 'low risk'  # Par défaut, définir le niveau de risque sur "low risk"
                recommendation = None  # Par défaut, pas de recommandation

            if proba > seuil_risque:
                transaction_risk = 'high risk'
            if not risque_email_envoye:
                recommendation = generate_recommendation(transaction_num, account_num)
                risque_email_envoye = True

                risques.append(transaction_risk)
                recommendations.append(recommendation)

                message = "<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ </h2></font>"
                message +="<font color='red'><h2><strong>Fraudulent Transaction Detected!</strong></h2></font>"
                message +="<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠</h2></font>"
                message +="<strong>Transaction Number:</strong> {}\n".format(transaction_num)
                message +="<strong>Account Number:</strong> {}\n".format(account_num)
            if recommendation is not None:
                # Create formatted recommendation with special characters for large size effect
                formatted_recommendation = "<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠</h2></font>"
                formatted_recommendation += "<h2><strong>RECOMMENDATION NEEDED</strong></h2>"
                formatted_recommendation += "<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠</h2></font>"
                formatted_recommendation += "<br>"
                formatted_recommendation += recommendation.upper()
                formatted_recommendation += "<br>"
                formatted_recommendation += "<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠</h2></font>"

                message += "<br>" + formatted_recommendation
                send_email(sender_email, sender_password, recipient_email, subject, transaction_num, account_num, message)
                block_account(account_num, test)
                email_sent_message = "Email sent successfully! Check your Email Please"
                block_account_message ="Account are temporarly blocked for suspision of fraud! Please Check up !!"
                recommendation_message ="It is recommended to inform the users of credit cards that they have to change their cards' passwords in order to avoid this kind of fraud next time"
                risque_email_envoye = True  # Mettre à jour l'état de l'envoi d'e-mail
            else:
                if proba > seuil_risque:
                    risques.append('high risk')
                    recommendation = generate_recommendation(transaction_num, account_num)
                    
                else:
                    if proba < seuil_risque:
                        risques.append('low risk')
                        recommendations.append(None)# No recommendation for non-fraudulent transactions
       
        # Afficher les résultats
        #for i, proba in enumerate(combined_probabilities):
        results = []
        for i, proba in enumerate(probabilities1):
            if i < len(test):
                transaction_num = str(test.iloc[i]['trans_num'])  # Accéder à la colonne 'trans_num' pour le numéro de transaction
                account_num = str(test.iloc[i]['cc_num'])  # Accéder à la colonne 'cc_num' pour le numéro de compte
                transaction_risk = risques[i] if i < len(risques) else 'unknown risk'

                print("Transaction {}: Probability of fraud: {:.4f}, Risk: {}".format(i+1, probabilities1[i][0] , transaction_risk))
                print("Transaction Number: {}, Account Number: {}".format(transaction_num, account_num))
                print()

            if transaction_risk == 'high risk':
                recommendation = recommendations[i] if i < len(recommendations) else None
                display(HTML("<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ RECOMMENDATION NEEDED ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠</h2></font>"))
            if recommendation is not None:
                display(HTML(recommendation.upper()))
            else:
                print("No recommendation available")
                display(HTML("<font color='red'><h2>⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠</h2></font>"))
         # Ajouter les résultats pour chaque transaction dans la liste 'results'
                results.append({
                    "transaction_num": transaction_num,
                    "account_num": account_num,
                    "transaction_risk": transaction_risk,
                    "recommendation": recommendation,
                })
                print(results)
            
        return render(request, 'search.html',{"block_account_message":block_account_message, "email_sent_message": email_sent_message,"recommendation_message":recommendation_message, "results": results})
    else:
        return render(request, 'search.html')





            
            
            
            
from django.http import JsonResponse          
import io       
import urllib, base64
    
    
   
    
    
    

















from django.shortcuts import render
import emna

#def notebook_view(request):
    # Execute your Python script or access any data
    #result = emna.execute()
    
    #context = {
        #'result': result
    #}
    
    #return render(request, 'recommendations.html', context)
    
import pandas as pd
import numpy as np
import spacy
import en_core_web_sm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import TruncatedSVD
import matplotlib.pyplot as plt
import wordcloud 
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from IPython.display import display
import pandas as pd
import numpy as np

import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import TruncatedSVD

import matplotlib.pyplot as plt
import wordcloud
from spacy.lang.en.stop_words import STOP_WORDS
from emna import print_similar_items
from emna import find_similar_items
import pickle
from .models import Formation







@login_required(login_url='login')
def notebook_view(request):
    
    item_id = request.GET.get('item_id')  # Retrieve the item ID from the GET request

    if item_id:
        item_id = int(item_id)
        # Execute the analysis code and get the desired result
        item_desc = print_similar_items(item_id)
        similar_item_ids = find_similar_items(item_id)
        
        
        result = Formation.objects.filter(id__in=similar_item_ids)
        
        item = Formation.objects.filter(id=item_id).first()
        item_rating = item.rating if item else None
    else:
        result = None
        item = None
        item_desc = None
        item_rating = None

    # Send the result, item, and item_id to your Django template
    context = {
        'result': result,
        'item': item,
        'item_id': item_id,
        'item_desc' :item_desc,
        'item_rating': item_rating,
        
        
    }

    return render(request, 'recommendations.html', context)
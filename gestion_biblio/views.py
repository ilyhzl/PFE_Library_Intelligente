from django.shortcuts import render, get_object_or_404
from .models import Livre, Emprunt, Etudiant
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Livre, Emprunt, Etudiant
from django.utils import timezone

# 1. Page d'accueil avec Système de Recommandation (IA Simple)
def home(request):
    tous_les_livres = Livre.objects.all()
    recommandations = []

    if request.user.is_authenticated:
        try:
            # Kan-choufo akher ktab sallafo had l-etudiant bach n-3rfo l-gout dialo
            dernier_emprunt = Emprunt.objects.filter(etudiant__user=request.user).latest('date_emprunt')
            ma_categorie = dernier_emprunt.livre.categorie
            
            # IA : Filtrage par contenu
            recommandations = Livre.objects.filter(categorie=ma_categorie).exclude(id=dernier_emprunt.livre.id)[:4]
        except:
            # Ila makan msallef walou, n-recommandiw lih akher ktub t-zadou
            recommandations = Livre.objects.all().order_by('-id')[:4]

    context = {
        'livres': tous_les_livres,
        'recommandations': recommandations,
    }
    return render(request, 'gestion_biblio/index.html', context)

# 2. Détails d'un livre
def detail_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    return render(request, 'gestion_biblio/detail.html', {'livre': livre})

# 3. Espace Etudiant
def mon_espace(request):
    if request.user.is_authenticated:
        mes_emprunts = Emprunt.objects.filter(etudiant__user=request.user)
        return render(request, 'gestion_biblio/espace_etudiant.html', {'emprunts': mes_emprunts})
    return render(request, 'registration/login.html')

# 4. Calculer les retards (Kif dertou f l-PDF)
def calculer_retards(request):
    today = timezone.now().date()
    emprunts_en_retard = Emprunt.objects.filter(date_retour_prevue__lt=today, statut='en cours')
    for emprunt in emprunts_en_retard:
        emprunt.statut = 'en retard'
        emprunt.save()
    return render(request, 'gestion_biblio/retards.html', {'count': emprunts_en_retard.count()})
def home(request):
    query = request.GET.get('q') # Kan-akhdou chno kteb l-etudiant f l-baht
    if query:
        # Kan-cherchiw f smit l-ktab ou l-auteur
        tous_les_livres = Livre.objects.filter(
            Q(titre__icontains=query) | Q(auteur__icontains=query)
        )
    else:
        tous_les_livres = Livre.objects.all()

    # Khalli l-baqi dial l-code dial l-recommandations kima houwa...
    recommandations = []
    if request.user.is_authenticated:
        try:
            dernier_emprunt = Emprunt.objects.filter(etudiant__user=request.user).latest('date_emprunt')
            recommandations = Livre.objects.filter(categorie=dernier_emprunt.livre.categorie).exclude(id=dernier_emprunt.livre.id)[:4]
        except:
            recommandations = Livre.objects.all().order_by('-id')[:4]

    context = {
        'livres': tous_les_livres,
        'recommandations': recommandations,
        'query': query,
    }
    return render(request, 'gestion_biblio/index.html', context)
 
def reserver_livre(request, id):
    livre = get_object_or_404(Livre, id=id)
    
    # Verifi wach l-etudiant m-connecter
    if not request.user.is_authenticated:
        return redirect('admin:login') # Ola l-page dial login ila 3ndk

    if livre.est_disponible:
        # 1. Ktab y-welli indisponible
        livre.est_disponible = False
        livre.save()

        # 2. Creeyi l-emprunt automatique
        # Hna khass n-l9aw l-etudiant li lié m3a l-user
        etudiant = Etudiant.objects.get(user=request.user)
        
        Emprunt.objects.create(
            etudiant=etudiant,
            livre=livre,
            date_retour_prevue=timezone.now().date() + timezone.timedelta(days=15), # 15 jours dial l-modda
            statut='en cours'
        )
        messages.success(request, f"Le livre '{livre.titre}' a été réservé avec succès !")
    
    return redirect('mon_espace') # Y-diih l-historique dialo bach y-chouf chno s-llef
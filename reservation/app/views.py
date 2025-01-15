from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from reservation import settings
from django.core.mail import send_mail,EmailMessage
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .token import generatorToken
from django.contrib.auth.decorators import user_passes_test,login_required
import json
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Reservation, Resource
from .forms import ReservationForm
from django.utils.encoding import force_str
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class ResourceListView(ListView):
    model = Resource
    template_name = 'app/resource_list.html'
    context_object_name = 'resources'

class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'app/reservation_form.html'
    success_url = reverse_lazy('resource_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ReservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'app/reservation_form.html'
    success_url = reverse_lazy('resource_list')

    def test_func(self):
        reservation = self.get_object()
        return self.request.user == reservation.user or self.request.user.is_staff

class ReservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Reservation
    template_name = 'app/reservation_confirm_delete.html'
    success_url = reverse_lazy('resource_list')

    def test_func(self):
        reservation = self.get_object()
        return self.request.user == reservation.user or self.request.user.is_staff



class ReservationListView(View):
    def get(self, request, *args, **kwargs):
        # Récupérer toutes les réservations
        reservations = Reservation.objects.filter(status='Reserved')
        reservation_list = []

        for reservation in reservations:
            reservation_list.append({
                'title': reservation.resource.name,
                'start': reservation.start_time.isoformat(),
                'end': reservation.end_time.isoformat(),
                'status': reservation.status
            })

        return JsonResponse(reservation_list, safe=False)


def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def manage_reservations(request):
    reservations = Reservation.objects.all()  # Un administrateur peut voir toutes les réservations
    return render(request, 'app/manage_reservations.html', {'reservations': reservations})


def home(request):
    return render(request, 'app/index.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        password = request.POST['password']
        password1 = request.POST['password1']

        if User.objects.filter(username=username):
            messages.error(request, "ce nom d'utilisateur est deja utilise")
            return redirect('register')
        
        if User.objects.filter(email=email):
            messages.error(request, "ce email possede deja un compte")
            return redirect('register')
        
        if not username.isalnum():
            messages.error(request, 'VOTRE NOM D UTILISATEUR DOIT CONTIENIR UNIQUEMENT DES CARACTERES ALPHANUMERIQUES')
            return redirect('register')
        
        if password!= password1:
            messages.error(request, 'LES MOTS DE PASSE NE SONT PAS IDENTIQUES')
            return redirect('register')

        mon_utilisateur = User.objects.create_user(username, email, password)
        mon_utilisateur.first_name = firstname
        mon_utilisateur.last_name = lastname
        mon_utilisateur.is_active = False
        mon_utilisateur.save()
        messages.success(request, 'VOTRE COMPTE A ETE CREER AVEC SUCCES')
        subject = "BIENVENUE DANS MON SYSTEME D'AUTHENTIFICATION DJANGO"
        message = "BIENVENUE" + mon_utilisateur.first_name + " " + mon_utilisateur.last_name + "\n HEUREUX DE VOUS COMPTER PARMI NOUS\n\n\n MERCI"
        from_email = settings.EMAIL_HOST_USER
        to_list = [mon_utilisateur.email]
        send_mail(subject, message, from_email, to_list, fail_silently=False)

        current_site = get_current_site(request)
        email_subject = "CONFIRMATION DE L'ADRESSE EMAIL"
        messageConfirm = render_to_string("emailconfirm.html",{
            "name": mon_utilisateur.first_name,
            "uid": urlsafe_base64_encode(force_bytes(mon_utilisateur.pk)),
            "token": generatorToken.make_token(mon_utilisateur),
            "domain": current_site.domain,
        })

        email = EmailMessage(
            email_subject,
            messageConfirm,
            settings.EMAIL_HOST_USER,
            [mon_utilisateur.email],
        )

        email.fail_silently = False
        email.send()
        return redirect('login')
    return render(request, 'app/register.html')

def logIn(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        my_user = User.objects.get(username=username)
        if user is not None:
              login(request,user)
              firstname = user.first_name
              return render(request, 'app/index.html',{'firstname':firstname})
        elif my_user.is_active == False:
            messages.error(request, 'VOTRE COMPTE N EST PAS ACTIF VEUILLEZ CONFIRMER VOTRE EMAIL DANS VOTRE BOITE MAIL')
            return redirect('login')
        else:
            messages.error(request, 'MAUVAISE AUTHENTIFICATION')
            return redirect('login')
    return render(request,'app/login.html')

def logOut(request):
    logout(request)
    messages.success(request, 'Vous avez ete deconnecte avec succes')
    return redirect('home')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and generatorToken.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'VOTRE COMPTE A ETE ACTIVE AVEC SUCCES')
        return redirect('login')
    else:
        messages.error(request, 'TOKEN INCORRECT')
        return redirect('home')





@login_required
def profile(request):
    user_reservations = Reservation.objects.filter(user=request.user)
    return render(request, 'app/profile.html', {'reservations': user_reservations})

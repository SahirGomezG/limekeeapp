import stripe

from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from .forms import ReservationForm

from .models import Reservations
from users.models import Profile
from django.contrib.auth.models import User
from django.db.models import Sum, F

from django.conf import settings
from django.views.generic.base import TemplateView

import time
from io import BytesIO
import base64
from matplotlib import pyplot as plt
import numpy as np

import calendar
import json

stripe_pub = settings.STRIPE_PUBLISHABLE_KEY
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_reservation_by_host(request):
    my_user_profile = User.objects.filter(username=request.user).first()
    bookings = Reservations.objects.filter(host=my_user_profile)
    return bookings


class ReservationListView(ListView):
    model = Reservations
    template_name = 'reservations/reservations_list.html'
    context_object_name = 'reservations'
    ordering = ['-check_in']
    paginate_by = 4

    def get_queryset(self):
        user = get_object_or_404(User, username = self.request.user)
        return Reservations.objects.filter(host=user).order_by('-check_in')

class UserReservationListView(ListView):
    model = Reservations
    template_name = 'reservations/reservations_list.html'
    context_object_name = 'reservations'
    paginate_by = 4

    def get_queryset(self):
        self.user = get_object_or_404(User, username = self.kwargs.get('username'))
        return Reservations.objects.filter(host=self.user).order_by('-check_in')


class ReservationDetailView(DetailView):
    model = Reservations          # queryset = Reservations.objects.all()
    template_name = 'reservations/reservations_detail.html'
    context_object_name = 'reservation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['key'] = stripe_pub
        return context

@login_required()
def charge(request,pk):
    reservation = Reservations.objects.get(confirmation_code = pk)
    this_user = User.objects.get(username=request.user)
    email = request.user.email

    if request.method == 'POST':
        try:
            charge = stripe.Charge.create(
                amount = 100*int(reservation.total_due),
                currency='usd',
                description=f'Reservation: {reservation.confirmation_code}',
                source=request.POST['stripeToken'],
                receipt_email=email,
            )
            reservation.paid = True
            reservation.save()

        except stripe.error.CardError as e:
            messages.warning(request, "Ops, sorry your card has been declined.")

    context = {
        'payment': reservation,
    }
    return render(request, 'reservations/reservations_charge.html',context)

class ReservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model= Reservations
    fields= [
        'paid',
    ]

    def form_valid(self,form):
        form.instance.host = self.request.user
        return super().form_valid(form)

    def test_func(self):
        reservation = self.get_object()
        if self.request.user == reservation.host:
            return True
        return False

@login_required()
def reservation_create_form (request):
    if request.user.has_perm('reservations.create_reservation'):
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            form = ReservationForm()
        context1 = {
            'form':form
        }
        return render (request,'reservations/reservation_create_form.html', context1)
    else:
        return redirect('reservation-home')


@login_required()
def summary (request):
    my_user_profile = User.objects.filter(username=request.user).first()
    context = {
        'reservations': Reservations.objects.filter(host=my_user_profile).order_by('-check_in')
        }
    return render(request, 'reservations/reservations_summary.html', context )

@login_required()
def metrics (request):
   date_data = Reservations.objects.filter(host=request.user).order_by('-check_in').values_list("check_in")
   payout_data = Reservations.objects.filter(host=request.user).values_list("price")

   plt.style.use('ggplot')

   plt.plot_date(date_data, payout_data, linestyle = 'solid')

   plt.gcf().autofmt_xdate()
   plt.title('My Payouts')
   plt.xlabel('Date')
   plt.ylabel('Payout ($)')

   plt.tight_layout()
   buffer = BytesIO()
   plt.savefig(buffer, format='png')
   buffer.seek(0)
   image_png = buffer.getvalue()
   buffer.close()
   plt.clf()

   graphic = base64.b64encode(image_png)
   graphic = graphic.decode('utf-8')

   return render(request, 'reservations/reservations_metrics.html', {'graphic':graphic})

class Progress(View):
    def get(self, request, *args, **kwargs):
        date = []
        payout =[]
        confirmation_code = []
        month_data = []
        month_list = [i.month for i in Reservations.objects.filter(host=request.user).order_by('check_in').values_list('check_in', flat=True)]

        # Convert month to String
        for mes in month_list:
            month_data.append(calendar.month_abbr[mes])

        for e in Reservations.objects.filter(host=request.user).order_by('check_in').values_list("price",flat=True):
            payout.append(int(e))
        for i in Reservations.objects.filter(host=request.user).order_by('check_in').values_list('check_in',flat=True):
            date.append(str(i))
        for code in Reservations.objects.filter(host=request.user).order_by('check_in').values_list('confirmation_code',flat=True):
            confirmation_code.append(str(code))

        # Dictionary of sum of Payouts by month
        payout_by_month = {}
        for key, value in zip(month_data,payout):
            try:
                payout_by_month[key] += value
            except KeyError:
                payout_by_month[key] = value

        payout_in_month = list(payout_by_month.values())
        month =list(payout_by_month.keys())

        return render(request, 'reservations/reservations_progress.html',
        {
            'labels': confirmation_code,
            'date' : date,
            'payout' : payout,
            'month': month,
            'payout_in_month': payout_in_month,
        })

class Calendar(View):
    def get(self, request, *args, **kwargs):
        guest = []
        check_in = []
        check_out = []

        reservations = Reservations.objects.filter(host=request.user).order_by('-check_in')
        for a in Reservations.objects.filter(host=request.user).order_by('check_in').values_list('guest',flat=True):
            guest.append(a)
        for i in Reservations.objects.filter(host=request.user).order_by('check_in').values_list('check_in',flat=True):
            check_in.append(str(i))
        for e in Reservations.objects.filter(host=request.user).order_by('check_in').values_list('check_out',flat=True):
            check_out.append(str(e))

        data = [{'title':title, 'start': start, 'end': end} for title, start, end in zip(guest, check_in, check_out)]
        json_data = json.dumps(data)

        return render(request, 'reservations/reservations_calendar.html',
        {
            'reservations': reservations,
            'data':json_data,
        })

@login_required()
def global_list (request):
    if request.user.has_perm('reservations.create_reservation'):
        context = {
            'reservations':Reservations.objects.all(),
            'users': Profile.objects.all()
            }
        return render(request, 'reservations/reservations_global.html', context )
    else:
        return redirect('reservation-home')

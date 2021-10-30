from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.contrib.auth.decorators import login_required
import pandas as pd
import plotly
import json
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries
import uuid
import os

from .models import *
from .functions import *


#api keys
ALPHA_KEY = os.environ.get("ALPHA_KEY")
if not ALPHA_KEY:
    raise RuntimeError("ALPHA_KEY not set")

IEX_KEY = os.environ.get("IEX_KEY")
if not IEX_KEY:
    raise RuntimeError("IEX_KEY not set")




class BuyForm(forms.Form):
    symbol = forms.CharField(label='', max_length=50, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" :" Symbol or Name", "id" : "symbol", "list" : "options", 'autocomplete' : "off"}))
    amount = forms.IntegerField(label='', min_value=1, widget=forms.NumberInput(attrs={"class" : "form-control", "placeholder" : "Amount"}))

class SellForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(SellForm, self).__init__(*args, **kwargs)
        self.fields['symbol'] = forms.ChoiceField(label='', choices=choices, widget=forms.Select(attrs={'class' : "form-control", "placeholder" : "Symbol"}))
        self.fields['amount'] = forms.IntegerField(label='', min_value=1, widget=forms.NumberInput(attrs={"class" : "form-control", "placeholder" : "Amount"}))
    
class QuoteForm(forms.Form):
    symbol = forms.CharField(label='', max_length=50, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" :"Symbol or Name", "id" : "symbol", "list" : "options", 'autocomplete' : "off"}))

class GroupLogin(forms.Form):
    key = forms.CharField(label='', max_length=7, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" :"Class Key", "autocomplete" : "off"}))

class GroupRegister(forms.Form):
    def __init__(self, *args, **kwargs):
        key = kwargs.pop('key')
        super(GroupRegister, self).__init__(*args, **kwargs)
        self.fields['name'] = forms.CharField(label='', max_length=100, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" : "Class Name", "autocomplete" : "off", "autofocus" : True}))
        self.fields['key'] = forms.CharField(label='', max_length=7, widget=forms.TextInput(attrs={"type" : 'hidden', "value" : key}))
        self.fields['cash'] = forms.DecimalField(label='', max_digits=9, decimal_places=2, min_value=0.00, widget=forms.NumberInput(attrs={"class" : "form-control", "placeholder" : "Starting Cash", "autocomplete" : "off"}))

class ChangePassword(forms.Form):
    new = forms.CharField(label='', widget=forms.PasswordInput(attrs={"class" : "form-control", "placeholder" : "New Password"}))
    confirmation = forms.CharField(label='', widget=forms.PasswordInput(attrs={"class" : "form-control", "placeholder" : "Confirm Password"}))

class AddCash(forms.Form):
    choices = [(1000, "$1,000"), (2500, "$2,500"), (5000, "$5,000"), (10000, "$10,000"), (15000, "$15,000"), (20000, "$20,000")]
    amount = forms.ChoiceField(label='', choices=choices, widget=forms.Select(attrs={'class' : "form-control", "placeholder" : "Amount"}))


def index(request):
    if request.user.is_authenticated:
        #get portfolio for who for the classroom function
        try:
            name = request.GET['user']
            user = User.objects.filter(username=name)
            user = user[0]
        except KeyError:
            user = request.user

        #get data 
        stocks = user.stocks.all()
        cash = usd(user.cash)
        totals = float(user.cash)
        s = []
        for stock in stocks:
            x = lookup(stock.symbol)
            x['amount'] = stock.amount
            i = stock.amount * x['price']
            totals += i
            x['total'] = usd(i)
            point = (x['price'] - x['prevClose']) / x['prevClose']
            point = point * 100
            point = round(point, 2)
            x['price'] = usd(x['price'])
            x['point'] = point
            s.append(x)

        totals = usd(totals)


        return render(request, "stocks/index.html", {
            "s" : s,
            'cash' : cash,
            "totals" : totals
        })
    else:
        return HttpResponseRedirect(reverse("login"))

def login_view(request):
    if request.method == "POST":

        #sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        #check if it is successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "stocks/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "stocks/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        try:
            teacher = request.POST['teacher']
        except KeyError:
            teacher = False

        #make sure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "stocks/register.html", {
                "message": "Passwords must match."
            })

        #create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            user.teacher = teacher
            user.save()
        except IntegrityError:
            return render(request, "stocks/register.html", {
                "message": "Username already taken."
            })

        login(request, user)

        return HttpResponseRedirect(reverse("index"))

    else:
        return render(request, "stocks/register.html")

@login_required
def buy(request):
    if request.method == "POST":
        #get and validate form data
        buy = BuyForm(request.POST)
        if buy.is_valid():
            stock = buy.cleaned_data['symbol']
            stock = stock.split(": ")[0]
            amount = buy.cleaned_data['amount']
            data = lookup(stock)

            #if stock is not on IEX
            if data is None:
                return render(request, "stocks/buy.html", {
                    "msg" : "Could not get data for this stock"
                })

            price = data['price']

            #check for over-spending
            if price * amount <= float(request.user.cash):
                transaction = Transaction(buyer=request.user, symbol=stock, price=price, amount=amount)

                #update data
                transaction.save()
                request.user.cash = float(request.user.cash) - (price * amount)
                request.user.save()
                x = Stocks.objects.filter(user=request.user, symbol=stock)
                if x:
                    x[0].amount += amount
                    x[0].save()
                else:
                    new = Stocks(user=request.user, symbol=stock, amount=amount)
                    new.save()
            else:
                return render(request, "stocks/buy.html", {
                "form" : buy,
            })

            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, "stocks/buy.html", {
                "form" : buy,
            })
    else:
        return render(request, "stocks/buy.html", {
            "form" : BuyForm(),
        })

@login_required
def sell(request):
    #get owned stocks
    stocks = Stocks.objects.filter(user=request.user)
    choices = []
    for stock in stocks:
        s = (stock.symbol, stock.symbol)
        choices.append(s)
    
    #get and validate form data
    if request.method == "POST":
        form = SellForm(request.POST, choices=choices)
        if form.is_valid():
            symbol = form.cleaned_data['symbol']
            amount = form.cleaned_data['amount']
            data = lookup(symbol)
            price = data['price']

            #update data
            x = Stocks.objects.filter(user=request.user, symbol=symbol)[0]
            if x.amount >= amount:
                transaction = Transaction(buyer=request.user, symbol=symbol, price=price, amount=-amount)
                transaction.save()
                request.user.cash = float(request.user.cash) + (price * amount)
                request.user.save()
                if x.amount - amount > 0:
                    i = x.amount - amount
                    x.amount = i
                    x.save()
                else:
                    x.delete()

                return HttpResponseRedirect(reverse('index'))
            else:
                return render(request, "stocks/sell.html", {
                    "form" : SellForm(choices=choices)
                })
        else:
            return render(request, "stocks/sell.html", {
                "form" : SellForm(choices=choices)
            })
    else:
        return render(request, "stocks/sell.html", {
            "form" : SellForm(choices=choices)
        })

@login_required
def history(request):

    #get user
    try:
        user = User.objects.filter(username = request.GET['user'])[0]
    except KeyError:
        user = request.user

    #get all transactions for the user
    stocks = Transaction.objects.filter(buyer=user).order_by("-date")
    
    return render(request, "stocks/history.html", {
        "stocks" : stocks,
    })

@login_required
def quote(request):
    #get and validate form data
    if request.method == "POST":
        form = QuoteForm(request.POST)
        if form.is_valid():

            symbol = form.cleaned_data['symbol']
            symbol = symbol.split(": ")
            symbol = symbol[0]
            quoteV = advancedLookup(symbol)

            try:
                #get day stats
                df = pd.read_json(f"https://cloud.iexapis.com/stable/stock/{symbol}/batch?types=intraday-prices&token={IEX_KEY}")
                df = df['intraday-prices']

                high = 0.00
                date = df[0]['date']
                low = df[0]['low']
                openS = df[0]['open']
                if len(df) == 390:
                    close = df[len(df)-1]['close']
                else:
                    close = None

                for i in range(len(df)):
                    #high
                    if high != None:
                        if df[i]['high'] != None:
                            if df[i]['high'] > high:
                                high = df[i]['high']
                    #low
                    if low != None:
                        if df[i]['low'] != None:
                            if df[i]['low'] < low:
                                low = df[i]['low']

                #get data for template
                price = quoteV["price"]
                price = usd(price)

                #news
                response = requests.get(f"https://cloud.iexapis.com/stable/stock/{symbol}/news/last/10?token={IEX_KEY}")
                
                return render(request, "stocks/quoted.html", {
                    "high" : high, 
                    "low" : low, 
                    "openS" : openS, 
                    "close" : close, 
                    "date" : date,
                    "quote" : quoteV,
                    "price" : price,
                    "news" : json.dumps(response.json())
                })
            except KeyError:
                return render(request, "stocks/quote.html", {
                    "msg" : "Could not get data for this stock."
                })
    else:
        return render(request, "stocks/quote.html", {
            "form" : QuoteForm(),
        })

@login_required
def groups(request):
    #group login
    if request.method == "POST":
        form = GroupLogin(request.POST)
        if form.is_valid():
            key = form.cleaned_data['key']
            group = Group.objects.filter(class_id=key)

            #add the user to the group
            try:
                group = group[0]
            except IndexError:
                return render(request, "stocks/groups_login.html", {
                "form" : form,
                "message" : "Invalid Class Key"
            })

            #update data
            group.member.add(request.user)
            group.save()
            request.user.is_in_group = True
            request.user.cash = group.cash
            request.user.save()

            return HttpResponseRedirect(reverse("groups"))
        else:
            return render(request, "stocks/groups_login.html", {
                "form" : form
            })
    else:
        #render group view
        if request.user.is_in_group:
            group = request.user.group.all()
            group = group[0]
            members = []

            #get the data for each member
            for member in group.member.all():
                stocks = member.stocks.all()
                totals = float(member.cash)
                for stock in stocks:
                    x = lookup(stock.symbol)
                    i = stock.amount * x['price']
                    totals += i
                temp = {"name" : member.username, "total" : totals}
                members.append(temp)

            #sort by totals
            members = sorted(members, key = lambda i: i['total'], reverse=True)

            #usd the totals
            for member in members:
                member['total'] = usd(member['total'])

            return render(request, "stocks/group.html", {
                "group" : group,
                "members" : members
            })
        else:
            return render(request, "stocks/groups_login.html", {
                "form" : GroupLogin()
            })

#leave a group
@login_required
def leave(request):
    #which group
    try:
        name = request.GET['name']
        user = request.GET['user']
    except KeyError:
        return HttpResponse(status=404)

    #leave the group
    user = User.objects.filter(username=user)[0]
    group = Group.objects.filter(name=name)
    group = group[0]
    group.member.remove(user)
    group.save()
    user.is_in_group = False
    user.save()

    #delete group if necessary
    if group.member.all().exists() == False:
        group.delete()
    
    return HttpResponseRedirect(reverse('groups'))
    

@login_required
def group_register(request):
    #creaet unique key
    key = ''
    unique = False
    while unique == False:
        key = str(uuid.uuid4())
        key = key[0:7]
        test = Group.objects.filter(class_id = key)
        try:
            test = test[0]
        except IndexError:
            unique = True

    #get and validate form data
    if request.method == "POST":
        form = GroupRegister(request.POST, key=request.POST['key'])
        if form.is_valid():
            name = form.cleaned_data['name']
            key = form.cleaned_data['key']
            cash = form.cleaned_data['cash']

            #create the group
            try:
                new = Group(name=name, class_id=key, cash=cash)
                new.save()
            except IntegrityError:
                return render(request, "stocks/g_register.html", {
                    "message": "Class name already taken.",
                    "form" : form,
                    "id" : key
                })

            #save data
            new.member.add(request.user)
            new.save()
            request.user.is_in_group = True
            request.user.cash = cash
            request.user.save()

            return HttpResponseRedirect(reverse("groups"))
        else:
            return render(request, "stocks/g_register.html", {
            "form" : form,
            "id" : key
        })
    else:
        return render(request, "stocks/g_register.html", {
            "form" : GroupRegister(key = key),
            "id" : key
        })

@login_required
def profile(request):
    #group status
    if request.user.is_in_group:
        group = request.user.group.all()
        group = group[0]
    else:
        group = None

    #get and validate form data for changing password
    if request.method == "POST" and "change" in request.POST:
        form = ChangePassword(request.POST)
        if form.is_valid():
            new = form.cleaned_data['new']
            confirm = form.cleaned_data['confirmation']

            #make sure passwords match
            if new != confirm:
                return render(request, "stocks/profile.html", {
                    "group" : group,
                    "form1" : form,
                    "message" : "Passwords do not match"
                })
            
            #update password
            request.user.set_password(new)
            request.user.save()
            
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request, "stocks/profile.html", {
                "group" : group,
                "form1" : form,
                "form2" : AddCash()
            })
    elif request.method == "POST" and "add" in request.POST:
        #form data for adding cash
        form = AddCash(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            #add cash
            request.user.cash = float(request.user.cash) + float(amount)
            request.user.save()

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "stocks/profile.html", {
                "group" : group,
                "form1" : ChangePassword(),
                "form2" : form
            })
    else:
        return render(request, "stocks/profile.html", {
            "group" : group,
            "form1" : ChangePassword(),
            "form2" : AddCash()
        })

@login_required
def graph(request, symbol):
    #get time series
    quote = lookup(symbol)
    ts = TimeSeries(ALPHA_KEY)
    data, meta = ts.get_daily_adjusted(symbol=symbol, outputsize="full")
    keys = data.keys()
    times = []
    for key in keys:
        times.append(key)
    closes = []
    for i in range(len(times)):
        closes.append(float(data[times[i]]['5. adjusted close']))
        #can cast to float if not working
    print(closes[0:3])
    #create the graph
    fig = px.area(x=times, y=closes, title=f'{quote["name"]} ({symbol}) Closing Prices')

    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
        buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(count=5, label="5y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    fig['data'][0]['line']['color']= "lightgray"
    
    return JsonResponse(plotly.io.to_html(fig, include_plotlyjs = False, full_html=False), safe=False)
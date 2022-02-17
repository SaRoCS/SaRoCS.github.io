from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import pandas as pd
import plotly
from urllib.error import HTTPError
import json
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries
import uuid
import os

from .forms import *
from .models import *
from .functions import *


#api keys
ALPHA_KEY = os.environ.get("ALPHA_KEY")
if not ALPHA_KEY:
    raise RuntimeError("ALPHA_KEY not set")

IEX_KEY = os.environ.get("IEX_KEY")
if not IEX_KEY:
    raise RuntimeError("IEX_KEY not set")

FMP_KEY = os.environ.get("FMP_KEY")
if not FMP_KEY:
    raise RuntimeError("FMP_KEY not set")


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
            "totals" : totals,
            "user" : user
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
                "msg" : "You do not have enough money"
            })

            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, "stocks/buy.html", {
                "form" : buy,
            })
    else:
        return render(request, "stocks/buy.html", {
            "form" : BuyForm(),
            "key" : FMP_KEY
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
                    "form" : SellForm(choices=choices),
                    "msg" : "You do not own this many shares"
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
                try:
                    df = pd.read_json(f"https://cloud.iexapis.com/stable/stock/{symbol}/batch?types=intraday-prices&token={IEX_KEY}")
                except HTTPError:
                    return render(request, "stocks/quote.html", {
                    "msg" : "Invalid symbol."
                }) 
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
                    if high is not None:
                        if df[i]['high'] is not None:
                            if df[i]['high'] > high:
                                high = df[i]['high']
                    #low
                    if low is not None:
                        if df[i]['low'] is not None:
                            if df[i]['low'] < low:
                                low = df[i]['low']

                #get data for template
                price = quoteV["price"]
                price = usd(price)

                #news
                #response = requests.get(f"https://cloud.iexapis.com/stable/stock/{symbol}/news/last/10?token={IEX_KEY}")
                
                return render(request, "stocks/quoted.html", {
                    "high" : high, 
                    "low" : low, 
                    "openS" : openS, 
                    "close" : close, 
                    "date" : date,
                    "quote" : quoteV,
                    "price" : price,
                    #"news" : json.dumps(response.json())
                })
            except KeyError:
                return render(request, "stocks/quote.html", {
                    "msg" : "Could not get data for this stock."
                })
    else:
        return render(request, "stocks/quote.html", {
            "form" : QuoteForm(),
            "key" : FMP_KEY
        })

@login_required
def classes(request):
    #class login
    if request.method == "POST":
        form = ClassLogin(request.POST)
        if form.is_valid():
            key = form.cleaned_data['key']
            cLass = Classroom.objects.filter(class_id=key)

            #add the user to the class
            try:
                cLass = cLass[0]
            except IndexError:
                return render(request, "stocks/class_login.html", {
                "form" : form,
                "message" : "Invalid Class Key"
            })

            #update data
            cLass.member.add(request.user)
            cLass.save()
            request.user.is_in_class = True
            request.user.cash += cLass.cash
            request.user.save()

            return HttpResponseRedirect(reverse("class"))
        else:
            return render(request, "stocks/class_login.html", {
                "form" : form
            })
    else:
        #render class view
        if request.user.is_in_class:
            cLass = request.user.classroom.all()
            cLass = cLass[0]
            members = []

            #get the data for each member
            for member in cLass.member.all():
                stocks = member.stocks.all()
                totals = float(member.cash)
                for stock in stocks:
                    x = lookup(stock.symbol)
                    i = stock.amount * x['price']
                    totals += i
                temp = {"user" : member, "total" : totals}
                members.append(temp)

            #sort by totals
            members = sorted(members, key = lambda i: i['total'], reverse=True)

            #get team names
            teams = list(request.user.classroom.all()[0].teams.all())

            join = [("None", "None")]
            score = []
            for team in teams:
                #team choices
                temp = (team.name, team.name)
                join.append(temp)

                #team score
                users = team.member.all()
                total = 0
                mems = 0
                for user in users:
                    for member in members:
                        if member['user'] == user:
                            total += member['total']
                            mems += 1
                total /= mems
                total -= float(team.classroom.cash)
                total = round(total / float(team.classroom.cash) * 100, 2)
                score.append({"team" : team.name, "score" : total})


            #usd the totals
            for member in members:
                member['total'] = usd(member['total'])

            return render(request, "stocks/class.html", {
                "class" : cLass,
                "members" : members,
                "form" : TeamForm(),
                "join_form" : JoinTeam(teams = join),
                'scores' : score
            })
        else:
            return render(request, "stocks/class_login.html", {
                "form" : ClassLogin()
            })

#leave a class
@login_required
def leave(request):
    #which class
    try:
        name = request.GET['name']
        user = request.GET['user']
    except KeyError:
        return HttpResponse(status=404)

    #leave the class
    user = User.objects.filter(username=user)[0]
    cLass = Classroom.objects.filter(name=name)
    cLass = cLass[0]
    cLass.member.remove(user)
    cLass.save()
    user.is_in_class = False
    user.cash -= cLass.cash
    user.save()

    #delete class if necessary
    if cLass.member.all().exists() == False:
        cLass.delete()
    
    return HttpResponseRedirect(reverse('class'))
    

@login_required
def class_register(request):
    #creaet unique key
    key = ''
    unique = False
    while unique == False:
        key = str(uuid.uuid4())
        key = key[0:7]
        test = Classroom.objects.filter(class_id = key)
        try:
            test = test[0]
        except IndexError:
            unique = True

    #get and validate form data
    if request.method == "POST":
        form = ClassRegister(request.POST, key=request.POST['key'])
        if form.is_valid():
            name = form.cleaned_data['name']
            key = form.cleaned_data['key']
            cash = form.cleaned_data['cash'] - 10000

            #create the class
            try:
                new = Classroom(name=name, class_id=key, cash=cash)
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
            request.user.is_in_class = True
            request.user.cash += cash
            request.user.save()

            return HttpResponseRedirect(reverse("class"))
        else:
            return render(request, "stocks/g_register.html", {
            "form" : form,
            "id" : key
        })
    else:
        return render(request, "stocks/g_register.html", {
            "form" : ClassRegister(key = key),
            "id" : key
        })

@login_required
def profile(request):
    #class status
    if request.user.is_in_class:
        cLass = request.user.classroom.all()
        cLass = cLass[0]
    else:
        cLass = None

    #get and validate form data for changing password
    if request.method == "POST" and "change" in request.POST:
        form = ChangePassword(request.POST)
        if form.is_valid():
            new = form.cleaned_data['new']
            confirm = form.cleaned_data['confirmation']

            #make sure passwords match
            if new != confirm:
                return render(request, "stocks/profile.html", {
                    "class" : cLass,
                    "form1" : form,
                    "message" : "Passwords do not match"
                })
            
            #update password
            request.user.set_password(new)
            request.user.save()
            
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request, "stocks/profile.html", {
                "class" : cLass,
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
                "class" : cLass,
                "form1" : ChangePassword(),
                "form2" : form
            })
    else:
        return render(request, "stocks/profile.html", {
            "class" : cLass,
            "form1" : ChangePassword(),
            "form2" : AddCash()
        })

@login_required
def graph(request, symbol):
    #get time series
    quote = lookup(symbol)
    ts = TimeSeries(ALPHA_KEY)
    #_adjusted
    data, meta = ts.get_weekly_adjusted(symbol=symbol) #outputsize="full"
    keys = data.keys()
    times = []
    for key in keys:
        times.append(key)
    closes = []
    for i in range(len(times)):
        #5. adjusted close
        closes.append(float(data[times[i]]['5. adjusted close']))#4. close
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

@login_required
def delete(request):
    request.user.delete()
    return HttpResponseRedirect(reverse('index'))

@login_required
def team(request):
    if request.method == "POST" and "color" in request.POST:
        form = TeamForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            color = form.cleaned_data['color']
            new = Team(name=name, color=color, classroom = request.user.classroom.all()[0])
            new.save()
            new.member.add(request.user)
            new.save()
            return HttpResponseRedirect(reverse("class"))
        else:
            pass
    elif request.method == "POST" and "team" in request.POST:
        #get team names
        teams = list(request.user.classroom.all()[0].teams.all())
        join = [("None", "None")]
        for team in teams:
            temp = (team.name, team.name)
            join.append(temp)
        
        #form
        form = JoinTeam(request.POST, teams = join)
        if form.is_valid():
            team_join = form.cleaned_data['team']
            if team_join != "None":
                classroom = request.user.classroom.all()[0]
                team = Team.objects.filter(name = team_join, classroom = classroom)[0]
                team.member.add(request.user)
                team.save()
            else:
                team = request.user.team.all()[0]
                team.member.remove(request.user)
            return HttpResponseRedirect(reverse("class"))
        else:
            pass
    else:
        raise Http404
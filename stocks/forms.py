from django import forms
from colorfield.fields import ColorField

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

class ClassLogin(forms.Form):
    key = forms.CharField(label='', max_length=7, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" :"Class Key", "autocomplete" : "off"}))

class ClassRegister(forms.Form):
    def __init__(self, *args, **kwargs):
        key = kwargs.pop('key')
        super(ClassRegister, self).__init__(*args, **kwargs)
        self.fields['name'] = forms.CharField(label='', max_length=100, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" : "Class Name", "autocomplete" : "off", "autofocus" : True}))
        self.fields['key'] = forms.CharField(label='', max_length=7, widget=forms.TextInput(attrs={"type" : 'hidden', "value" : key}))
        self.fields['cash'] = forms.DecimalField(label='', max_digits=9, decimal_places=2, min_value=0.00, widget=forms.NumberInput(attrs={"class" : "form-control", "placeholder" : "Starting Cash", "autocomplete" : "off"}))

class ChangePassword(forms.Form):
    new = forms.CharField(label='', widget=forms.PasswordInput(attrs={"class" : "form-control", "placeholder" : "New Password"}))
    confirmation = forms.CharField(label='', widget=forms.PasswordInput(attrs={"class" : "form-control", "placeholder" : "Confirm Password"}))

class AddCash(forms.Form):
    choices = [(1000, "$1,000"), (2500, "$2,500"), (5000, "$5,000"), (10000, "$10,000"), (15000, "$15,000"), (20000, "$20,000")]
    amount = forms.ChoiceField(label='', choices=choices, widget=forms.Select(attrs={'class' : "form-control", "placeholder" : "Amount"}))


class TeamForm(forms.Form):
    name = forms.CharField(label='', max_length=100, widget=forms.TextInput(attrs={"class" : "form-control", "placeholder" : "Team Name", "autocomplete" : "off", "autofocus" : True}))
    color = forms.CharField(label='Team color', widget=forms.TextInput(attrs={"class" : "form-control", "type" : "color"}))

class JoinTeam(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('teams')
        super(JoinTeam, self).__init__(*args, **kwargs)
        self.fields['team'] = forms.ChoiceField(label='Choose a team', choices=choices, widget=forms.Select(attrs={'class' : "form-control", "placeholder" : "Team", "form" : "join", "onchange" : "this.form.submit()"}))
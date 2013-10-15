# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.


from django import forms
from django.utils import html
from lizard_security.models import UserGroup
from lizard_registration.models import Organisation
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.core.validators import validate_email


def organisations():
    """Returns list of organisations."""
    organisations = Organisation.objects.all()
    choices = []
    for organisation in organisations:
        choices.append((organisation.id, organisation.name))
    return choices


class UserSetPasswordForm(SetPasswordForm):
    """Form contains a hidden fields to check a user."""
    token = forms.CharField(widget=forms.HiddenInput())
    uid_base = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.token = kwargs['token']
        self.uid_base = kwargs['uid_base']
        kwargs.pop('token')
        kwargs.pop('uid_base')
        super(UserSetPasswordForm, self).__init__(*args, **kwargs)
        self.fields["token"].initial = self.token
        self.fields["uid_base"].initial = self.uid_base


class CreateUserForm(forms.Form):
    """Form to create and activate a user."""

    def __init__(self, *args, **kwargs):
        self.groups_queryset = kwargs['groups_queryset']
        kwargs.pop('groups_queryset')
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields['groups'].queryset = self.groups_queryset


    username = forms.CharField(max_length=30,
                               label='Gebruikersnaam')
    first_name = forms.CharField(max_length=30,
                                 label='Voornaam',
                                 required=False)
    last_name = forms.CharField(max_length=30,
                                label='Achternaam',
                                required=False)
    email = forms.EmailField(max_length=200, label='E-mail', required=True)

    groups = forms.ModelMultipleChoiceField(label='GebruikersGroepen',
                                            required=False,
                                            queryset=UserGroup.objects.none(),
                                            widget=forms.CheckboxSelectMultiple())

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(u'%s already exists' % username)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        users = User.objects.filter(email=email)
        if users.exists():
            raise forms.ValidationError(u'%s already exists' % email)
        return email



class UpdateUserForm(CreateUserForm):
    """Form contains the fields to manage a user."""
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs['user_id']
        kwargs.pop('user_id')
        super(UpdateUserForm, self).__init__(*args, **kwargs)

    is_active = forms.BooleanField(required=False, label='Actief')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
            if self.user_id == unicode(user.id):
                return username
        except User.DoesNotExist:
            return username

        raise forms.ValidationError(u'%s already exists' % username )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            users = User.objects.get(email=email)
            if self.user_id == unicode(users.id):
                return email
        except User.DoesNotExist:
            return email
        except User.MultipleObjectsReturned:
            raise forms.ValidationError(u'%s already exists' % email)

        raise forms.ValidationError(u'%s already exists' % email)


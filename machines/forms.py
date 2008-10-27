from django import forms
from django.conf import settings

from karaage.projects.models import Project

from models import MachineCategory, Machine


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine



class UserAccountForm(forms.Form): 
    username = forms.CharField()
    machine_category = forms.ModelChoiceField(queryset=MachineCategory.objects.all(), initial=1)
    default_project = forms.ModelChoiceField(queryset=Project.active.all())


    def clean(self):
        data = self.cleaned_data
        if data['default_project'].machine_category != data['machine_category']:
            raise forms.ValidationError(u'Default project not in machine category')
        return data

class ShellForm(forms.Form):

    shell = forms.ChoiceField(choices=settings.SHELLS)

    def save(self, user=None):

        if user is None:
            user = get_current_user().get_profile()


        from accounts.ldap_utils.ldap_users import change_shell
        change_shell(user, self.cleaned_data['shell'])

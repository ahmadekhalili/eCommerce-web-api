from django import forms

import json

from customed_files.states_towns import list_states_towns

    
class shipping_town_widget(forms.Select):
    template_name = 'orders/widgets/shipping_town_select.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)       
        context['towns_states'] = [[L[0], json.dumps(L[1])] for L in list_states_towns]   #[(('1', 'tehran'), json.dumps((('3', 'shahriar'), ('4', 'karaj')))), (('2', 'qom'), json.dumps((('5', 'qom1'), ('6', 'qom2'))))]        
        context['value'] = value
        return context


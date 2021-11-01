from django.core.management.base import BaseCommand, CommandError
from main.models import State

import time

from customed_files.states_towns import list_states_towns



class Command(BaseCommand):
    help = 'create states and its towns'

    def handle(self, *args, **options):
        states = []
        for L in list_states_towns:
            states.append(State(key=L[0][0], name=L[0][1], towns=L[1]))
        
        State.objects.bulk_create(states)  
        self.stdout.write(self.style.SUCCESS('Successfully created all {} states and its towns'.format(len(states))))

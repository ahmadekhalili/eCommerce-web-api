from django.core.management.base import BaseCommand, CommandError
from main.models import State, Town

import time

from customed_files.states_towns import list_states_towns



class Command(BaseCommand):
    help = 'create states and its towns'

    def handle(self, *args, **options):
        states, towns = [], []
        for L in list_states_towns:
            states.append(State(key=L[0][0], name=L[0][1]))
            for town in L[1]:
                towns.append(Town(key=town[0], name=town[1], state_id=L[0][0]))
        
        State.objects.bulk_create(states)
        Town.objects.bulk_create(towns)
        self.stdout.write(self.style.SUCCESS('Successfully created all {} states and its towns'.format(len(states))))

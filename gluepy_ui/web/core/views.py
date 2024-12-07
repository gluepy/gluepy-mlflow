from django.shortcuts import render
from django.views.generic import ListView
from .models import Run


class RunListView(ListView):
    model = Run
    template_name = 'core/run_list.html'
    context_object_name = 'runs'

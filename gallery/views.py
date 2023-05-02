from django.shortcuts import render
# from flask import Flask, render_template, request
import os
import csv
from .models import City, Gallery
from .forms import CityForm

# app = Flask(__name__)
# data_file_path = os.path.join('data', 'data/gallery.csv')
# @app.route('/', methods=['GET', 'POST'])

def index(request):
    form = CityForm
    context = {'form': form, }
    if request.method == 'POST':
        form = CityForm(request.POST)
        thiscity = request.POST['mycity']
        if form.is_valid():
            gallery_list = Gallery.objects.filter(city=thiscity)
            context = {'gallery_list': gallery_list, 'city': thiscity,}
            return render(request, 'gallery/result.html', context)
    return render(request, 'gallery/index.html', context)

def result(request):
    return None



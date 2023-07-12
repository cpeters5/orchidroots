from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import os
from django.conf import settings
# from flask import Flask, render_template, request
import csv
from .models import City, Gallery, Artist, Artwork, Genre, Medium
from .forms import CityForm, UploadFileForm


# app = Flask(__name__)
# data_file_path = os.path.join('data', 'data/gallery.csv')
# @app.route('/', methods=['GET', 'POST'])

def index(request):
    genre_list = Artwork.objects.exclude(genre='NA').values_list('genre', flat=True).distinct().order_by('genre')
    medium_list = Artwork.objects.exclude(medium='NA').values_list('medium', flat=True).distinct().order_by('medium')
    genre = ''
    medium = ''
    if 'genre' in request.POST:
        genre = request.POST['genre']
        if genre and genre != '':
            try:
                genre = Genre.objects.get(genre=genre)
            except Genre.DoesNotExist:
                genre = ''
    if 'medium' in request.POST:
        medium = request.POST['medium']
        if medium and medium != '':
            try:
                medium = Medium.objects.get(medium=medium)
            except Genre.DoesNotExist:
                medium = ''

    # Get a sample image of orchids
    artwork_list = Artwork.objects.filter(rank__lt=7).filter(rank__gt=0)
    artwork_list = artwork_list.order_by('-rank', '?')[0:3]
    print("artwork_list = ", len(artwork_list))
    context = {'artwork_list': artwork_list, 'genre': genre, 'medium': medium,
               'genre_list': genre_list, 'medium_list': medium_list,
               }
    return render(request, 'gallery/index.html', context)


def browse_gallery(request):
    genre_list = Artwork.objects.exclude(genre='NA').values_list('genre', flat=True).distinct().order_by('genre')
    medium_list = Artwork.objects.exclude(medium='NA').values_list('medium', flat=True).distinct().order_by('medium')
    genre = ''
    medium = ''
    if 'genre' in request.POST:
        genre = request.POST['genre']
        if genre and genre != '':
            try:
                genre = Genre.objects.get(genre=genre)
            except Genre.DoesNotExist:
                genre = ''
    if 'medium' in request.POST:
        medium = request.POST['medium']
        if medium and medium != '':
            try:
                medium = Medium.objects.get(medium=medium)
            except Genre.DoesNotExist:
                medium = ''

    # Get a sample image of orchids
    artwork_list = Artwork.objects.filter(rank__lt=7).filter(rank__gt=0)
    if genre and genre != 'NA':
        artwork_list = artwork_list.filter(genre=genre)
    if medium and medium != 'NA':
        artwork_list = artwork_list.filter(medium=medium)
    artwork_list = artwork_list.order_by('-rank', '?')[0:6]
    print("artwork_list = ", len(artwork_list))
    context = {'artwork_list': artwork_list, 'genre': genre, 'medium': medium,
               'genre_list': genre_list, 'medium_list': medium_list,
               }
    return render(request, 'gallery/browse_gallery.html', context)


def my_gallery(request):
    genre_list = Artwork.objects.exclude(genre='NA').values_list('genre', flat=True).distinct().order_by('genre')
    medium_list = Artwork.objects.exclude(medium='NA').values_list('medium', flat=True).distinct().order_by('medium')
    genre = ''
    medium = ''
    artist = ''
    if request.user.is_authenticated:
        try:
            artist = Artist.objects.get(artist=request.user)
        except Artist.DoesNotExist:
            artist = ''

    if 'genre' in request.POST:
        genre = request.POST['genre']
        if genre and genre != '':
            try:
                genre = Genre.objects.get(genre=genre)
            except Genre.DoesNotExist:
                genre = ''
    if 'medium' in request.POST:
        medium = request.POST['medium']
        if medium and medium != '':
            try:
                medium = Medium.objects.get(medium=medium)
            except Genre.DoesNotExist:
                medium = ''

    # Get a sample image of orchids
    if artist:
        artwork_list = Artwork.objects.filter(artist=artist)
    else:
        artwork_list = Artwork.objects.filter(rank__lt=7).filter(rank__gt=0)
    if genre and genre != 'NA':
        artwork_list = artwork_list.filter(genre=genre)
    if medium and medium != 'NA':
        artwork_list = artwork_list.filter(medium=medium)
    artwork_list = artwork_list.order_by('-rank', '?')[0:6]

    context = {'artist': artist, 'artwork_list': artwork_list, 'genre': genre, 'medium': medium,
               'genre_list': genre_list, 'medium_list': medium_list,
               }
    return render(request, 'gallery/my_gallery.html', context)


def browse_artist(request):
    genre_list = Artwork.objects.exclude(genre='NA').values_list('genre', flat=True).distinct().order_by('genre')
    medium_list = Artwork.objects.exclude(medium='NA').values_list('medium', flat=True).distinct().order_by('medium')
    genre = ''
    medium = ''
    artist = ''
    city = ''
    if 'genre' in request.POST:
        genre = request.POST['genre']
        if genre and genre != '':
            try:
                genre = Genre.objects.get(genre=genre)
            except Genre.DoesNotExist:
                genre = ''
    if 'medium' in request.POST:
        medium = request.POST['medium']
        if medium and medium != '':
            try:
                medium = Medium.objects.get(medium=medium)
            except Genre.DoesNotExist:
                medium = ''

    if 'city' in request.GET:
        city = request.GET['city']
        if city and city != '':
            try:
                city = City.objects.get(city=city)
            except City.DoesNotExist:
                city = ''

    artist_list = Artist.objects.all()
    if medium:
        artist_list = artist_list.filter(media__icontains=medium)
    if city:
        artist_list = artist_list.filter(city=city)

    artist_list_sample = []
    for artist in artist_list:
        sample_image = Artwork.objects.filter(artist=artist).order_by('-rank', '?')[0:1][0]
        artist_list_sample = artist_list_sample + [[artist, sample_image]]
        print("artist = ", artist)
        print("sample = ", sample_image.image_file)
    artist_list = artist_list_sample
    context = {'artist_list': artist_list, 'medium_list': medium_list, 'medium': medium,}
    return render(request, 'gallery/browse_artist.html', context)

    # Now we get artist_list of sample genera


def photos(request):
    print("Start rendering photos ")
    if 'artist' in request.GET:
        artist = request.GET['artist']
        print(artist)
    else:
        message = 'Must have artist name'
        print("no artist")
        return HttpResponse(message)
    print(settings.MEDIA_ROOT)
    path = '/gallery/artworks'
    path = settings.MEDIA_ROOT
    print(path)
    try:
        artist = Artist.objects.get(pk=artist)
        print(artist)
    except Artist.DoesNotExist:
        print("no artist")
        return HttpResponseRedirect('/')
    artwork_list = Artwork.objects.filter(artist=artist.artist)
    print(len(artwork_list))
    context = {'artist': artist, 'artwork_list': artwork_list, 'path': path,
               }
    return render(request, 'gallery/photos.html', context)


def uploadfile(request):
    print("Start rendering upload file")
    form = UploadFileForm(request.POST or None)
    path = '/gallery/artworks'
    context = {'form': form}
    artist = ''
    if 'artist' in request.POST:
        artist = request.POST['artist']
    try:
        artist = Artist.objects.get(pk=artist)
    except Artist.DoesNotExist:
        return render(request, 'gallery/uploadfile.html', context)
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            spc = form.save(commit=False)
            spc.artist = artist
            spc.save()
            send_url = '/gallery/photos/?artist=' + str(artist)
            return HttpResponseRedirect(send_url)
            # context = {'artist': artist, 'path': path}
            # return render(request, 'gallery/photos.html', context)

    return render(request, 'gallery/uploadfile.html', context)

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings
# from flask import Flask, render_template, request
import csv
from .models import City, Gallery, Artist, Artwork, Genre, Medium
from .forms import CityForm, UploadFileForm, UpdateFileForm


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
    artwork_list = Artwork.objects.filter(rank__lt=7).filter(rank__gt=0).exclude(artist='test')
    artwork_list = artwork_list.order_by('-rank', '?')[0:3]
    # print("artwork_list = ", len(artwork_list))
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
        genre = request.POST.get('genre', '')
    if not genre or genre == '':
        genre = request.GET.get('genre', '')

    print("genre", genre)
    if genre and genre != '':
        try:
            genre = Genre.objects.get(genre=genre)
        except Genre.DoesNotExist:
            genre = ''
    if 'medium' in request.POST:
        medium = request.POST.get('medium', '')
        if not medium:
            medium = request.GET.get('medium', '')
        if medium and medium != '':
            try:
                medium = Medium.objects.get(medium=medium)
            except Genre.DoesNotExist:
                medium = ''

    # Get a sample image of orchids
    artwork_list = Artwork.objects.filter(rank__lt=7, rank__gt=0).exclude(artist='test')
    print("genre", genre)
    if genre and genre != '':
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
    if 'artist' in request.GET:
        artist = request.GET['artist']

    if request.user.is_authenticated:
        try:
            artist = Artist.objects.get(artist=artist)
        except Artist.DoesNotExist:
            artist = ''
    # print("type artist = ", type(artist))
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
    if request.user.is_authenticated and artist:
        artwork_list = Artwork.objects.filter(artist=artist).filter(rank__gt=0)
    elif request.user.is_authenticated and request.user.artist:
        artwork_list = Artwork.objects.filter(artist=request.user.artist).filter(rank__gt=0)
    elif artist:
        artwork_list = Artwork.objects.filter(rank__gt=0).filter(artist=artist)
    else:
        artwork_list = Artwork.objects.filter(rank__gt=0).exclude(artist='test')

    if genre and genre != 'NA':
        artwork_list = artwork_list.filter(genre=genre)
    if medium and medium != 'NA':
        artwork_list = artwork_list.filter(medium=medium)
    artwork_list = artwork_list.order_by('-rank', '?')

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

    artist_list = Artist.objects.exclude(artist='test')
    if medium:
        artist_list = artist_list.filter(media__icontains=medium)
    if city:
        artist_list = artist_list.filter(city=city)

    artist_list_sample = []
    for artist in artist_list:
        sample_image = Artwork.objects.filter(artist=artist).order_by('-rank', '?')[0:1]
        if len(sample_image) < 1:
            sample_image = ''
        else:
            sample_image = sample_image[0]
        artist_list_sample = artist_list_sample + [[artist, sample_image]]
        # print("artist = ", artist)
    artist_list = artist_list_sample
    context = {'artist_list': artist_list, 'medium_list': medium_list, 'genre_list': genre_list, 'medium': medium,}
    return render(request, 'gallery/browse_artist.html', context)


def detail(request, id):
    genre_list = Artwork.objects.exclude(genre='NA').values_list('genre', flat=True).distinct().order_by('genre')
    medium_list = Artwork.objects.exclude(medium='NA').values_list('medium', flat=True).distinct().order_by('medium')
    try:
        image = Artwork.objects.get(pk=id)
    except Artwork.DoesNotExist:
        # print("incorrect requested image")
        return HttpResponseRedirect('/')
    context = {'image': image, 'genre_list': genre_list, 'medium_list': medium_list,
               }
    return render(request, 'gallery/detail.html', context)


def uploadfile(request):
    # print("Start rendering upload file")
    artist = ''
    if 'artist' in request.POST:
        artist = request.POST['artist']
    elif 'artist' in request.GET:
        artist = request.GET['artist']
    elif request.user.is_authenticated:
        artist = request.user.artist.artist
    else:
        artist = 'NEW'
    if artist:
        try:
            artist = Artist.objects.get(pk=artist)
        except Artist.DoesNotExist:
            return render(request, 'gallery/uploadfile.html', context)
    form = UploadFileForm(initial={'artist': artist, 'price': 0})
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            spc = form.save(commit=False)
            spc.artist = artist
            spc.save()
            send_url = '/gallery/my_gallery/?artist=' + str(artist)
            return HttpResponseRedirect(send_url)

    context = {'form': form, 'artist': artist}
    return render(request, 'gallery/uploadfile.html', context)


@login_required
def deletephoto(request, id):
    next = ''
    try:
        image = Artwork.objects.get(pk=id)
    except Artwork.DoesNotExist:
        message = 'This image does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    image_dir = image.image_dir()
    filename = os.path.join(settings.MEDIA_ROOT, str(image.image_file))
    # print("filename = ", filename)
    image.delete()
    artist = image.artist
    if 'next' in request.GET:
        next = request.GET['next']
    if next == 'my_gallery':
        url = "%s?artist=%s" % (reverse('gallery:my_gallery'), artist)
    else:
        url = "%s" % (reverse('common:curate_newupload'))

    # Finally remove file if exist
    if os.path.isfile(filename):
        os.remove(filename)
    return HttpResponseRedirect(url)


def updatefile(request, id):
    try:
        image = Artwork.objects.get(pk=id)
    except Artwork.DoesNotExist:
        message = 'This image does not exist! Use arrow key to go back to previous page.'
        return HttpResponse(message)
    artist = image.artist
    image_file = image.image_file
    form = UpdateFileForm(instance=image)
    if request.method == 'POST':
        form = UpdateFileForm(request.POST)
        if form.is_valid():
            spc = form.save(commit=False)
            spc.artist = artist
            spc.id = image.id
            spc.image_file = image_file
            print("artist = ", spc.artist)
            spc.save()
            send_url = '/gallery/my_gallery/?artist=' + str(artist)
            return HttpResponseRedirect(send_url)
    context = {'form': form, 'image': image, }
    return render(request, 'gallery/updatefile.html', context)


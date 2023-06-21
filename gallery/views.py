from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import os
from django.conf import settings
# from flask import Flask, render_template, request
import csv
from .models import City, Gallery, Artist, Artwork
from .forms import CityForm, UploadFileForm


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


def browse_artist(request):
    # Application must be in request
    artist = ''
    alpha = ''
    if 'alpha' in request.GET:
        alpha = request.GET['alpha']

    # app must be in browse request
    app = request.GET['app']
    if 'artist' in request.GET:
        artist = request.GET['artist']
    #     If app is requested, find artist_list and sample image by artist
    # If artist is requested, get sample list by genera
    if 'media' in request.GET:
        # App and artist must also be in the request.
        Media = apps.get_model(app.lower(), 'Media')
        Species = apps.get_model(app.lower(), 'Species')
        media = request.GET['artist']
        if media and media != '':
            try:
                media = Media.objects.get(media=media)
            except Media.DoesNotExist:
                Media = ''
            if Media:
                species = Species.objects.filter(media=media)
                if talpha:
                    species = species.filter(species__istartswith=talpha)
                species = species.order_by('species')
                if len(species) > 500:
                    species = species[0: 500]
                species_list = []
                for x in species:
                    spcimage = x.get_best_img()
                    if spcimage:
                        species_list = species_list + [spcimage]
                context = {'species_list': species_list, 'artist': media.artist, 'app': media.artist.application, 'media': media, 'talpha': talpha, 'alpha_list': alpha_list,}
                return render(request, 'common/newbrowse.html', context)
    if artist:
        try:
            artist = Artist.objects.get(artist=artist)
        except Artist.DoesNotExist:
            artist = None
        if artist:
            Media = apps.get_model(app.lower(), 'Media')
            SpcImages = apps.get_model(app.lower(), 'SpcImages')
            # genera = Media.objects.filter(artist=artist)
            genera = SpcImages.objects.order_by('gen').values_list('gen', flat=True)
            if genera:
                media_list = []
                genera = set(genera)
                genlist = Media.objects.filter(pid__in=genera)
                if talpha:
                    genlist = genlist.filter(media__istartswith=talpha)
                genlist = genlist.order_by('media')
                for gen in genlist:
                    media_list = media_list + [gen.get_best_img()]
                context = {'media_list': media_list, 'artist': artist, 'app': artist.application, 'talpha': talpha, 'alpha_list': alpha_list,}
                return render(request, 'common/newbrowse.html', context)

    # Building sample by artists
    artists = Artist.objects.filter(application=app)
    if talpha:
        artists = artists.filter(artist__istartswith=talpha)
    artists = artists.order_by('artist')
    Media = apps.get_model(app.lower(), 'Media')
    artist_list = []
    for fam in artists:
        genimage = Media.objects.filter(artist=fam.artist)
        genimage = genimage.order_by('?')[0:1]
        if len(genimage) > 0:
            artist_list = artist_list + [(genimage[0], genimage[0].get_best_img())]
    context = {'artist_list': artist_list, 'app': app, 'talpha': talpha, 'alpha_list': alpha_list,}
    return render(request, 'common/newbrowse.html', context)

    # Bad application, and neither artists nor media are valid, list all genera in the app
    write_output(request, str(artist))
    return HttpResponseRedirect('/')

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

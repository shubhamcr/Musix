from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .forms import UserForm, AlbumForm, SongForm
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Album, Song

AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg', 'gif']


def create_album(request):
    if not request.user.is_authenticated():
        return redirect('music:index')
    else:
        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.album_logo = request.FILES['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, 'music/create_album.html', context)
            album.save()
            return render(request, 'music/detail.html', {'album': album})
        context = {
            "form": form,
        }
        return render(request, 'music/create_album.html', context)

def create_song(request, album_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    form = SongForm(request.POST or None, request.FILES or None)
    album = get_object_or_404(Album, pk=album_id)
    if form.is_valid():
        albums_songs = album.song_set.all()
        for s in albums_songs:
            if s.song_title == form.cleaned_data.get("song_title"):
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'You already added that song',
                }
                return render(request, 'music/create_song.html', context)
        song = form.save(commit=False)
        song.album = album
        song.audio_file = request.FILES['audio_file']
        file_type = song.audio_file.url.split('.')[-1]
        file_type = file_type.lower()
        if file_type not in AUDIO_FILE_TYPES:
            context = {
                'album': album,
                'form': form,
                'error_message': 'Audio file must be WAV, MP3, or OGG',
            }
            return render(request, 'music/create_song.html', context)

        song.save()
        return redirect('music:detail', album_id)
    context = {
        'album': album,
        'form': form,
    }
    return render(request, 'music/create_song.html', context)


def delete_album(request, album_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    album = Album.objects.get(pk=album_id)
    album.delete()
    #albums = Album.objects.filter(user=request.user)
    return redirect('music:userprofile', pk=request.user.pk)


def delete_song(request, album_id, song_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    album = get_object_or_404(Album, pk=album_id)
    song = Song.objects.get(pk=song_id)
    song.delete()
    return redirect('music:detail', album_id)


def detail(request, album_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    else:
        user = request.user
        album = get_object_or_404(Album, pk=album_id)
        return render(request, 'music/detail.html', {'album': album, 'user': user})


def favorite(request, song_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    song = get_object_or_404(Song, pk=song_id)
    try:
        if song.is_favorite:
            song.is_favorite = False
        else:
            song.is_favorite = True
        song.save()
    except (KeyError, Song.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})


def favorite_album(request, album_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    album = get_object_or_404(Album, pk=album_id)
    try:
        if album.is_favorite:
            album.is_favorite = False
        else:
            album.is_favorite = True
        album.save()
    except (KeyError, Album.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})

def index(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                #albums = Album.objects.filter(user=request.user)
                return redirect('music:userprofile', pk=user.pk)
            else:
                return render(request, 'music/index.html', {'error': 'Your account has been disabled'})
        else:
            return render(request, 'music/index.html', {'error': 'Invalid login'})
    return render(request, 'music/index.html', {})


def userprofile(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not request.user.is_authenticated():
        return redirect('music:index')
    else:
        albums = Album.objects.filter(user=request.user)
        song_results = Song.objects.all()
        query = request.GET.get("q")
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
                ).distinct()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
                ).distinct()
            return render(request, 'music/userprofile.html', {
                'albums': albums,
                'songs': song_results,
                })
        else:
            return render(request, 'music/userprofile.html', {'albums': albums})


def search_user(request):
    if not request.user.is_authenticated():
        return redirect('music:index')
    albums = Album.objects.filter(user=request.user)
    username = request.GET.get('username')
    user_searched = User.objects.filter(username=username)
    if User.objects.filter(username=username).exists():
        user_searched_albums = Album.objects.filter(user=user_searched)
        context = {
            'user': request.user, 
            'albums': albums, 
            'user_searched': user_searched, 
            'user_searched_albums': user_searched_albums,
            'user_searched_username': username,
        }
        return render(request, 'music/search_user.html', context)
    return render(request, 'music/search_user.html', {'error': 'Username does not exist.'})


def search_user_album_detail(request, album_id):
    if not request.user.is_authenticated():
        return redirect('music:index')
    else:
        user = request.user
        # albums = Album.objects.filter(user=user)
        album = get_object_or_404(Album, pk=album_id)
        return render(request, 'music/search_user_album_detail.html', {'user': user, 'album': album})


def register(request):
	if request.method == 'POST':
		form = UserForm(request.POST)
		username = request.POST.get('username')
		password1 = request.POST.get('password1')
		password2 = request.POST.get('password2')
		email = request.POST.get('email')
		if User.objects.filter(username=username).exists():
			return render(request, 'music/register.html', {"form": form, "error": 'Username already taken.'})
		if username and email and password1 and password2:
			if password1 == password2:
				if form.is_valid():
					user = form.save(commit=False)
					username = form.cleaned_data['username']
					password1 = form.cleaned_data['password1']
					user.set_password(password1)
					user.save()
					user = authenticate(username=username, password=password1)
					if user is not None:
						if user.is_active:
							login(request, user)
							# albums = Album.objects.filter(user=request.user)
							return redirect('music:userprofile', pk=user.pk) #{'albums': albums})
						context = {
							"form": form,
							"error": 'User account is disabled. Please contact the administrator.',
						}
						return render(request, 'music/register.html', context) 
					context = {
						"form": form,
						"error": 'User not authenticated. Please try again.'
					}
					return render(request, 'music/register.html', context) 

			else:
				context = {
				"form": form,
				"error": 'Passwords do not match. Please try again.',
				}
				return render(request, 'music/register.html', context)
		else:
			context = {
			"form": form,
			"error": 'Fill all the fields',
			}    
			return render(request, 'music/register.html', context)
	else:
		form = UserForm()
		context = {
			"form": form,
			"error": '',
		}
		return render(request, 'music/register.html', context)

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                #albums = Album.objects.filter(user=request.user)
                return redirect('music:userprofile', pk=user.pk)
            else:
                return render(request, 'music/index.html', {'error': 'Your account has been disabled'})
        else:
            return render(request, 'music/index.html', {'error': 'Invalid login'})
    return render(request, 'music/index.html')

def logout_user(request):
    logout(request)
    return redirect('music:index')


def songs(request, filter_by):
    if not request.user.is_authenticated():
        return redirect('music:index')
    else:
        try:
            song_ids = []
            for album in Album.objects.filter(user=request.user):
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids)
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'song_list': users_songs,
            'filter_by': filter_by,
        })




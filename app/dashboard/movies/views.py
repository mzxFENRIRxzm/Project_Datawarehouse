import ast
import json
import time
from urllib.parse import parse_qsl

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Movie

EVENT_STREAM_SUBSCRIBERS = []


def _seed_movies():
    sample_movies = [
        {
            'title': 'Inception',
            'rating': 9.8,
            'poster_url': 'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=800&q=80',
        },
        {
            'title': 'Dune',
            'rating': 9.1,
            'poster_url': 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80',
        },
        {
            'title': 'Avatar',
            'rating': 8.9,
            'poster_url': 'https://images.unsplash.com/photo-1542204165-65bf26472b9b?auto=format&fit=crop&w=800&q=80',
        },
        {
            'title': 'Interstellar',
            'rating': 8.7,
            'poster_url': 'https://images.unsplash.com/photo-1478720568477-152d9b164e26?auto=format&fit=crop&w=800&q=80',
        },
        {
            'title': 'The Dark Knight',
            'rating': 9.4,
            'poster_url': 'https://images.unsplash.com/photo-1513106580091-1d82408b8cd6?auto=format&fit=crop&w=800&q=80',
        },
    ]

    for item in sample_movies:
        Movie.objects.get_or_create(title=item['title'], defaults=item)


def dashboard(request):
    if not Movie.objects.exists():
        _seed_movies()

    movies = Movie.objects.order_by('-rating')
    context = {
        'movies': movies,
        'top_movie': movies.first(),
    }
    return render(request, 'movies/dashboard.html', context)


def _extract_post_data(request):
    if request.content_type and request.content_type.startswith('application/json'):
        try:
            return json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return {}

    body = request.body.decode('utf-8', errors='ignore') if request.body else ''

    if hasattr(request, 'POST') and request.POST:
        payload = request.POST
        if isinstance(payload, dict) and payload.get('rating') is not None:
            return payload

        if hasattr(payload, 'get') and payload.get('rating') is not None:
            return payload

        if body:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

            try:
                parsed = ast.literal_eval(body)
                if isinstance(parsed, dict):
                    return parsed
            except (SyntaxError, ValueError):
                pass

            if '=' in body:
                return dict(parse_qsl(body, keep_blank_values=True))

        return payload

    if body:
        if body.startswith('{') or body.startswith('['):
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(body)
                except (SyntaxError, ValueError):
                    pass

        if '=' in body:
            return dict(parse_qsl(body, keep_blank_values=True))

    return {}


@csrf_exempt
def movie_api(request, movie_id):
    movie = Movie.objects.get(id=movie_id)

    if request.method == 'POST':
        payload = _extract_post_data(request)
        if not isinstance(payload, dict):
            payload = {}

        rating = payload.get('rating')
        if rating is None:
            return JsonResponse({'error': 'rating is required'}, status=400)

        try:
            movie.rating = float(rating)
            movie.save(update_fields=['rating', 'updated_at'])
        except (TypeError, ValueError):
            return JsonResponse({'error': 'rating must be a number'}, status=400)

        for subscriber in list(EVENT_STREAM_SUBSCRIBERS):
            try:
                subscriber.write(f"event: movie-update\ndata: {json.dumps({'id': movie.id, 'title': movie.title, 'rating': movie.rating})}\n\n")
                subscriber.flush()
            except Exception:
                pass

    return JsonResponse({
        'id': movie.id,
        'title': movie.title,
        'rating': movie.rating,
        'updated_at': movie.updated_at.isoformat(),
    })


def movie_events(request):
    def event_stream():
        try:
            yield 'retry: 1000\n\n'
            EVENT_STREAM_SUBSCRIBERS.append(response)
            while True:
                time.sleep(1)
                yield ': ping\n\n'
        except GeneratorExit:
            pass
        finally:
            if response in EVENT_STREAM_SUBSCRIBERS:
                EVENT_STREAM_SUBSCRIBERS.remove(response)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream; charset=utf-8')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    return response

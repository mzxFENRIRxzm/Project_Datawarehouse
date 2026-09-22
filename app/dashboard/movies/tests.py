import json

from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Movie
from .views import movie_api, movie_events


class MovieDashboardTests(TestCase):
    def test_movie_rating_is_stored_and_displayed(self):
        Movie.objects.create(title='Inception', rating=8.4)

        response = self.client.get(reverse('movies:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inception')

    def test_movie_api_returns_current_score(self):
        movie = Movie.objects.create(title='Dune', rating=9.1)

        response = self.client.get(reverse('movies:movie_api', args=[movie.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Dune')
        self.assertEqual(response.json()['rating'], 9.1)

    def test_dashboard_creates_seed_movies_when_empty(self):
        Movie.objects.all().delete()

        response = self.client.get(reverse('movies:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Movie.objects.exists())
        self.assertContains(response, 'Live Movie Poster Scoreboard')

    def test_movie_api_accepts_external_rating_update(self):
        movie = Movie.objects.create(title='Interstellar', rating=8.7)
        request = RequestFactory().post(
            reverse('movies:movie_api', args=[movie.id]),
            {'rating': 9.6},
            content_type='application/x-www-form-urlencoded',
        )

        response = movie_api(request, movie.id)

        self.assertEqual(response.status_code, 200)
        movie.refresh_from_db()
        self.assertEqual(movie.rating, 9.6)
        self.assertEqual(json.loads(response.content.decode())['rating'], 9.6)

    def test_root_redirects_to_movies_dashboard(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/movies/'))

    def test_sse_endpoint_exposes_event_stream(self):
        request = RequestFactory().get('/movies/events/')
        response = movie_events(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream; charset=utf-8')

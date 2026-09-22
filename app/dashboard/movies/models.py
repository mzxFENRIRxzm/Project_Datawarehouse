from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=200)
    rating = models.FloatField(default=0.0)
    poster_url = models.URLField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

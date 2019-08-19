from django.core.cache import cache
from django.urls import reverse
from django.utils.html import format_html


def image_url_cache_key(image_id, spec):
    return f'image_url_cache_{image_id}_{spec}'


def generate_image_url(image, filter_spec):
    cache_key = image_url_cache_key(image.id, filter_spec)
    url = cache.get(cache_key)
    if url:
        return url
    from wagtail.images.views.serve import generate_signature
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    url += image.file.name[len('original_images/'):]
    cache.set(cache_key, url)
    return url


def generate_image_tag(image, filter_spec):
    url = generate_image_url(image, filter_spec)
    return format_html(f'<img alt="{image.title}" src="{url}">')

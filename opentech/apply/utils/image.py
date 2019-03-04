from django.urls import reverse
from django.utils.html import format_html


def generate_image_url(image, filter_spec):
    from wagtail.images.views.serve import generate_signature
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    url += image.file.name[len('original_images/'):]
    return format_html(f'<img alt="{image.title}" src="{url}">')

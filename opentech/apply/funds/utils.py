from opentech.apply.utils.image import generate_image_tag


def render_icon(image):
    if not image:
        return ''
    filter_spec = 'fill-20x20'
    return generate_image_tag(image, filter_spec)

from elevate.decorators import elevate_required


class ElevateMixin:
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return elevate_required(view)

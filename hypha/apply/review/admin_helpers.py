from wagtail.contrib.modeladmin.helpers import PageButtonHelper


class ButtonsWithClone(PageButtonHelper):
    def clone_button(self, obj, classnames_add, classnames_exclude):
        classname = self.copy_button_classnames + classnames_add
        cn = self.finalise_classname(classname, classnames_exclude)
        return {
            "url": self.url_helper.get_action_url("clone", instance_pk=obj.pk),
            "label": "Clone",
            "classname": cn,
            "title": "Clone this %s" % self.verbose_name,
        }

    def get_buttons_for_obj(
        self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        btns = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )

        # Put preview before delete
        btns.insert(-1, self.clone_button(obj, classnames_add, classnames_exclude))

        return btns

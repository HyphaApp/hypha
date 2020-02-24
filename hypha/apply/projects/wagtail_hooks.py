from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ManageAdminGoup


modeladmin_register(ManageAdminGoup)

#!/usr/bin/env python
"""
Script that creates a superuser for review apps in Kubernetes.
See kubernetes/run.sh for details.
"""

import os

import django
from django.contrib.auth import get_user_model


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opentech.settings")
django.setup()

User = get_user_model()
username = 'admin'
password = 'admin'
email = 'admin@localhost'

if not User.objects.filter(username=username, email=email).exists():
    User.objects.create_superuser(username=username, email=email, password=password)

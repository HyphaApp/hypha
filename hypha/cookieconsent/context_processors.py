def cookies_accepted(request):
    cookieconsent = False
    if request.COOKIES.get("cookieconsent", "decline") == "accept":
        cookieconsent = True

    return {"COOKIES_ACCEPTED": cookieconsent}

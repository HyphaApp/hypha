import requests

from django.conf import settings


class SlackNotifications():

    def __init__(self):
        self.destination = settings.SLACK_DESTINATION_URL
        self.target_room = settings.SLACK_DESTINATION_ROOM

    def __call__(self, *args, recipients=None, related=None, **kwargs):
        return self.send_message(*args, recipients=None, related=related, **kwargs)

    def slack_users(self, users):
        slack_users = []
        for user in users:
            if user.slack:
                slack_users.append(f'<{user.slack}>')
        return ' '.join(slack_users)

    def slack_link(self, request, related, path=None, **kwargs):
        try:
            url = path or related.get_absolute_url()
        except AttributeError:
            return ''

        link = request.scheme + '://' + request.get_host() + url
        title = str(related)
        return f'<{link}|{title}>'

    def send_message(self, message, request, recipients=None, related=None, **kwargs):
        if not self.destination or not self.target_room:
            errors = list()
            if not self.destination:
                errors.append('Destination URL')
            if not self.target_room:
                errors.append('Room ID')
            return 'Missing configuration: {}'.format(', '.join(errors))

        slack_users = self.slack_users(recipients) if recipients else ''

        slack_link = self.slack_link(request, related, **kwargs) if related else ''

        message = ' '.join([slack_users, message, slack_link]).strip()

        data = {
            "room": self.target_room,
            "message": message,
        }
        response = requests.post(self.destination, json=data)

        return str(response.status_code) + ': ' + response.content.decode()


slack_notify = SlackNotifications()

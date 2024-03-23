from django.conf import settings
from django.contrib import messages

from hypha.apply.activity.options import MESSAGES

neat_related = {
    MESSAGES.DETERMINATION_OUTCOME: "determination",
    MESSAGES.BATCH_DETERMINATION_OUTCOME: "determinations",
    MESSAGES.UPDATE_LEAD: "old_lead",
    MESSAGES.NEW_REVIEW: "review",
    MESSAGES.TRANSITION: "old_phase",
    MESSAGES.BATCH_TRANSITION: "transitions",
    MESSAGES.APPLICANT_EDIT: "revision",
    MESSAGES.EDIT_SUBMISSION: "revision",
    MESSAGES.COMMENT: "comment",
    MESSAGES.SCREENING: "old_status",
    MESSAGES.REVIEW_OPINION: "opinion",
    MESSAGES.DELETE_REVIEW: "review",
    MESSAGES.DELETE_REVIEW_OPINION: "review_opinion",
    MESSAGES.EDIT_REVIEW: "review",
    MESSAGES.CREATED_PROJECT: "submission",
    MESSAGES.PROJECT_TRANSITION: "old_stage",
    MESSAGES.APPROVE_PAF: "paf_approvals",  # expect a list
    MESSAGES.UPDATE_PROJECT_LEAD: "old_lead",
    MESSAGES.APPROVE_CONTRACT: "contract",
    MESSAGES.UPLOAD_CONTRACT: "contract",
    MESSAGES.CREATE_INVOICE: "create_invoice",
    MESSAGES.UPDATE_INVOICE_STATUS: "invoice",
    MESSAGES.APPROVE_INVOICE: "invoice",
    MESSAGES.DELETE_INVOICE: "invoice",
    MESSAGES.UPDATE_INVOICE: "invoice",
    MESSAGES.SUBMIT_REPORT: "report",
    MESSAGES.SKIPPED_REPORT: "report",
    MESSAGES.REPORT_FREQUENCY_CHANGED: "config",
    MESSAGES.REPORT_NOTIFY: "report",
    MESSAGES.CREATE_REMINDER: "reminder",
    MESSAGES.DELETE_REMINDER: "reminder",
    MESSAGES.REVIEW_REMINDER: "reminder",
    MESSAGES.BATCH_UPDATE_INVOICE_STATUS: "invoices",
}


class AdapterBase:
    messages = {}
    always_send = False

    def message(self, message_type, **kwargs):
        try:
            message = self.messages[message_type]
        except KeyError:
            # We don't know how to handle that message type
            return

        try:
            # see if its a method on the adapter
            method = getattr(self, message)
        except AttributeError:
            return self.render_message(message, **kwargs)
        else:
            # Delegate all responsibility to the custom method
            return method(**kwargs)

    def render_message(self, message, **kwargs):
        return message.format(**kwargs)

    def extra_kwargs(self, message_type, **kwargs):
        return {}

    def get_neat_related(self, message_type, related):
        # We translate the related kwarg into something we can understand
        try:
            neat_name = neat_related[message_type]
        except KeyError:
            # Message type doesn't expect a related object
            if related:
                raise ValueError(
                    f"Unexpected 'related' kwarg provided for {message_type}"
                ) from None
            return {}
        else:
            if not related:
                raise ValueError(f"{message_type} expects a 'related' kwarg")
            return {neat_name: related}

    def recipients(self, message_type, **kwargs):
        raise NotImplementedError()

    def batch_recipients(self, message_type, sources, **kwargs):
        # Default batch recipients is to send a message to each of the recipients that would
        # receive a message under normal conditions
        return [
            {
                "recipients": self.recipients(message_type, source=source, **kwargs),
                "sources": [source],
            }
            for source in sources
        ]

    def process_batch(
        self, message_type, events, request, user, sources, related=None, **kwargs
    ):
        events_by_source = {event.source.id: event for event in events}
        for recipient in self.batch_recipients(
            message_type, sources, user=user, **kwargs
        ):
            recipients = recipient["recipients"]
            sources = recipient["sources"]
            events = [events_by_source[source.id] for source in sources]
            self.process_send(
                message_type,
                recipients,
                events,
                request,
                user,
                sources=sources,
                source=None,
                related=related,
                **kwargs,
            )

    def process(
        self, message_type, event, request, user, source, related=None, **kwargs
    ):
        recipients = self.recipients(
            message_type,
            source=source,
            related=related,
            user=user,
            request=request,
            **kwargs,
        )
        self.process_send(
            message_type,
            recipients,
            [event],
            request,
            user,
            source,
            related=related,
            **kwargs,
        )

    def process_send(
        self,
        message_type,
        recipients,
        events,
        request,
        user,
        source,
        sources=None,
        related=None,
        **kwargs,
    ):
        if sources is None:
            sources = []
        try:
            # If this was a batch action we want to pull out the submission
            source = sources[0]
        except IndexError:
            pass

        kwargs = {
            "request": request,
            "user": user,
            "source": source,
            "sources": sources,
            "related": related,
            **kwargs,
        }
        kwargs.update(self.get_neat_related(message_type, related))
        kwargs.update(self.extra_kwargs(message_type, **kwargs))

        message = self.message(message_type, **kwargs)
        if not message:
            return

        for recipient in recipients:
            message_logs = self.create_logs(message, recipient, *events)

            if settings.SEND_MESSAGES or self.always_send:
                status = self.send_message(
                    message, recipient=recipient, logs=message_logs, **kwargs
                )
            else:
                status = "Message not sent as SEND_MESSAGES==FALSE"

            message_logs.update_status(status)

            if not settings.SEND_MESSAGES:
                if recipient:
                    debug_message = "{} [to: {}]: {}".format(
                        self.adapter_type, recipient, message
                    )
                else:
                    debug_message = "{}: {}".format(self.adapter_type, message)
                messages.add_message(request, messages.DEBUG, debug_message)

    def create_logs(self, message, recipient, *events):
        from ..models import Message

        messages = Message.objects.bulk_create(
            Message(**self.log_kwargs(message, recipient, event)) for event in events
        )
        return Message.objects.filter(id__in=[message.id for message in messages])

    def log_kwargs(self, message, recipient, event):
        return {
            "type": self.adapter_type,
            "content": message,
            "recipient": recipient or "",
            "event": event,
        }

    def send_message(self, message, **kwargs):
        # Process the message, should return the result of the send
        # Returning None will not record this action
        raise NotImplementedError()

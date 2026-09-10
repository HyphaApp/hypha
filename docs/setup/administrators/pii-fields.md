# Marking form fields as personal information

Application forms often ask for details that identify the applicant personally —
a phone number, a home address, a date of birth. Hypha lets you mark those
questions so that only the people who genuinely need the answers can read them.

Set `PII_FIELD_MARKING_ENABLED=True` to turn the feature on.

## Marking a field

With the setting enabled, every question block in the form builder (Wagtail
Admin → "Apply" → "Forms") gains a **"Personal information"** checkbox. Tick it
on any question whose answer will contain personally identifiable information.

The checkbox is empty by default, so no existing question changes behaviour when
you turn the feature on.

## Who can see the answers

Answers to marked questions are shown to:

 * the applicant who created the submission
 * the co-applicants invited to that submission
 * staff (and staff admins)

Everyone else — including reviewers, external reviewers and community reviewers
— sees the question, but the answer is replaced with "Hidden — contains personal
information." Keeping the question visible means reviewers can still tell what
was asked and that an answer exists.

## Built-in fields

The built-in required fields (Title, Full name, E-mail, Address, Organization
name, Requested funding and Duration) do not have the checkbox. Applicant
identity in those fields is controlled separately by
[`HIDE_IDENTITY_FROM_REVIEWERS`](configuration.md).

## Turning the feature off again

Setting `PII_FIELD_MARKING_ENABLED=False` hides the checkbox in the form builder
but does **not** un-hide fields that have already been marked. This is
deliberate: turning the setting off should never silently expose information
that was marked as personal. To make an answer visible again, turn the setting
back on and untick the checkbox on that question.

Note that changing a form only affects submissions made from then on. Each
submission stores its own copy of the form it was filled in with, so existing
submissions keep the marks they were submitted with.

## Limitations

Answers are indexed for search regardless of whether they are marked, so a
search by a reviewer can still match on the text of a hidden answer. The search
results themselves only show submission titles, never the matched answer.

Redaction applies to the submission page and everywhere the answers are shown on
it, including the answers panel embedded in the review and determination forms.

The other places answers appear are restricted to staff already, so nothing is
redacted there: the submission PDF download, the revision comparison view, and
CSV exports (the last also governed by `SUBMISSIONS_EXPORT_ACCESS_STAFF` and
`SUBMISSIONS_EXPORT_ACCESS_STAFF_ADMIN`).

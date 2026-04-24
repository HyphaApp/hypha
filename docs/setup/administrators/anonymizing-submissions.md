# Anonymizing Submissions

Hypha offers submission anonymization to allow for less retention of Personally Identifiable Information (PII).

When the configuration option `SUBMISSION_ANONYMIZATION_ENABLED=True`, submissions can be either:

 * Individually anonymized (Submission Detail View → "More Actions" → "Anonymize" button)
 * Anonymized manually in bulk (Submissions All View → select submissions → "Anonymize" button in actions bar)
 * Anonymized in bulk via user deletion (Wagtail Admin → "Settings" → "Users" → Select a user → "…" in top action/nav bar → "Delete" → "Anonymize all user submissions")
 * Anonymized through the management command `python3 manage.py submission_cleanup --submissions [days]` (more info on that [here](cron-jobs.md#submission-cleanup))

When a submission is anonymized, the original submission is deleted and a derivative is created with the following attributes:

 * `value` - applied for value (if it exists on the original submission)
 * `status` - status of the original submission
 * `page` - either the fund/lab that the original submission existed on
 * `round` - round (if any) the original submission was in
 * `submit_time` - time the original submission was submitted
 * `screening_status` - screening status of the original submission
 * `category` - the categories of the original submission

 and if the user that "owns" the submission still exists and isn't being actively deleted:

 * `user` - stores the user that "owned" the original submission. When the user account is deleted, this field is set to null.

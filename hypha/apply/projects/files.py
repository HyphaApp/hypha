def flatten(iterable):
    """Flatten the given iterable into an iterable of non-list items"""
    for item in iterable:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


def get_files(project):
    """
    Get files from the given Project's Submission.

    A Submission can have fields which contain multiple files, these are
    returned from Submission.data as a list meaning the given fields can be in
    the form of:

        [obj1, [obj2, obj3]]

    This function will flatten this providing a single level iterable:

        [obj1, obj2, obj3]

    """
    file_field_names = project.submission.file_field_ids
    file_fields = (project.submission.data(field) for field in file_field_names)

    return list(flatten(file_fields))

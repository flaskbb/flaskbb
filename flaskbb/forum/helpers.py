def get_forum_ids(forum):
    """
    Returns a list of forum ids for the passed `forum` object and its child hierarchy.
    """
    forum_ids = [forum.id]
    if forum.children:
        for child in forum.children:
            forum_ids.extend(
                get_forum_ids(child)
            )
    return forum_ids

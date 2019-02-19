# -*- coding: utf-8 -*-
"""
    flaskbb.forum.services.update
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forum update services.

    :copyright: (c) 2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

import attr

from ...core.exceptions import accumulate_errors
from ...core.changesets import ChangeSetHandler
from ...utils.database import try_commit


@attr.s(cmp=False, frozen=True, repr=True, hash=False)
class TopicUpdateHandler(ChangeSetHandler):
    """
    Validates and updates a topic and persists the changes to the
    database.
    """

    db = attr.ib()
    plugin_manager = attr.ib()

    def apply_changeset(self, model, changeset):
        accumulate_errors(
            lambda v: v.validate(model, changeset), self.validators
        )
        changeset.assign_to_topic(model)
        try_commit(self.db.session, "Could not update topic")
        self.plugin_manager.hook.flaskbb_topic_updated(
            user=model, details_update=changeset
        )

from bridgekeeper import perms
from bridgekeeper.rules import R
from django.utils.timezone import now

from pretalx.person.permissions import can_change_submissions, is_reviewer

is_event_visible = R(is_public=True)


perms['cfp.view_event'] = is_event_visible | (can_change_submissions | is_reviewer)
perms['cfp.add_speakers'] = (
    R(submission_type__deadline__isnull=True, event__cfp__deadline__isnull=True)  # no deadline at all
    | R(submission_type__deadline__isnull=False, submission_type__deadline__gte=now)  # TODO: now()
    | R(submission_type__deadline__isnull=True, event__cfp__deadline__isnull=False, event__cfp__deadline__gte=now)  # TODO: now()
)

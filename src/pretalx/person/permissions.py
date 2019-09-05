from bridgekeeper import perms
from bridgekeeper.rules import R, blanket_rule, is_authenticated

from pretalx.submission.models.submission import SubmissionStates

@blanket_rule
def is_administrator(user):
    return getattr(user, 'is_administrator', False)


can_change_submissions = is_authenticated & (
    is_administrator
    | R(organiser__teams=(R(members__in=lambda user: [user], can_change_submissions=True, all_events=True)))
    | R(team_set=(R(members__in=lambda user: [user], can_change_submissions=True, all_events=False)))
)
is_reviewer = is_authenticated & R(event__teams=R(members__in=lambda user: [user], is_reviewer=True))
person_can_view_information = is_authenticated & (
    R(include_submitters=True, event__submissions__speakers__in=lambda user: [user])
    | R(include_submitters=False, exclude_unconfirmed=True, event__submissions=R(speakers__in=lambda user: [user], state=SubmissionStates.CONFIRMED))
    | R(include_submitters=False, exclude_unconfirmed=False, event__submissions=R(speakers__in=lambda user: [user], submissions__state__in=[SubmissionStates.CONFIRMED, SubmissionStates.ACCEPTED]))
)

perms['person.is_administrator'] = is_administrator
perms['person.view_information'] = can_change_submissions | person_can_view_information
perms['person.change_information'] = can_change_submissions

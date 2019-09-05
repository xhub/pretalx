from bridgekeeper import perms
from bridgekeeper.rules import R, is_authenticated
from django.db.models import Q

from pretalx.person.permissions import can_change_submissions, is_reviewer
from pretalx.submission.models import SubmissionStates

has_submissions = is_authenticated & R(submissions__speakers__in=lambda user: [user])
is_speaker = is_authenticated & R(speakers__in=lambda user: [user])


can_be_withdrawn = R(state__in=SubmissionStates.valid_previous_states[SubmissionStates.WITHDRAWN])
can_be_rejected = R(state__in=SubmissionStates.valid_previous_states[SubmissionStates.REJECTED])
can_be_accepted = R(state__in=SubmissionStates.valid_previous_states[SubmissionStates.ACCEPTED])
can_be_confirmed = R(state__in=SubmissionStates.valid_previous_states[SubmissionStates.CONFIRMED])
can_be_canceled = R(state__in=SubmissionStates.valid_previous_states[SubmissionStates.CANCELED])
can_be_removed = R(state__in=SubmissionStates.valid_previous_states[SubmissionStates.DELETED])
can_be_edited = (
    (R(state=SubmissionStates.SUBMITTED) & (
        R(event__cfp__is_open=True)
        | R(event__review_phases=R(is_active=True, speakers_can_change_submissions=True))
    ))
    | (R(state__in=[SubmissionStates.ACCEPTED, SubmissionStates.CONFIRMED]))
)
is_review_author = is_authenticated & R(user=lambda user: user)
can_be_reviewed = is_authenticated & R(
    state=SubmissionStates.SUBMITTED,
    event__review_phases=R(is_active=True, can_review=True)
)
can_view_all_reviews = is_authenticated & R(event__review_phases=R(is_active=True, can_see_other_reviews='always'))
can_view_reviews = (
    is_authenticated
    & (
        can_view_all_reviews
        | R(event__review_phases=R(is_active=True, can_see_other_reviews='after_review'), reviews__user=lambda user: user)
    )
)

#@rules.predicate
def has_reviewer_access(user, obj):  # TODO bridgekeeper: howww?
    from pretalx.submission.models import Submission

    if hasattr(obj, 'submission'):
        obj = obj.submission
    if not isinstance(obj, Submission):
        raise Exception('Incorrect use of reviewer permissions')
    result = user.teams.filter(
        Q(Q(all_events=True) | Q(limit_events__in=[obj.event]))
        & Q(Q(limit_tracks__isnull=True) | Q(limit_tracks__in=[obj.track])),
        is_reviewer=True,
    )
    return result.exists()


reviewer_can_change_submissions = R(event__review_phases=R(is_active=True, can_change_submission_state=True))

perms['submission.accept_or_reject_submissions'] = can_change_submissions | (is_reviewer & reviewer_can_change_submissions)
perms['submission.perform_actions'] = is_speaker
perms['submission.withdraw_submission'] = can_be_withdrawn & is_speaker
perms['submission.reject_submission'] = can_be_rejected & (can_change_submissions | (is_reviewer & reviewer_can_change_submissions))
perms['submission.accept_submission'] = can_be_accepted & (can_change_submissions | (is_reviewer & reviewer_can_change_submissions))
perms['submission.confirm_submission'] = can_be_confirmed & (is_speaker | can_change_submissions)
perms['submission.cancel_submission'] = can_be_canceled & (is_speaker | can_change_submissions)
perms['submission.remove_submission'] = can_be_removed & can_change_submissions
perms['submission.edit_submission'] = (can_be_edited & is_speaker) | can_change_submissions
#perms['submission.view_submission'] = is_speaker | can_change_submissions | has_reviewer_access
#perms['submission.review_submission'] = has_reviewer_access & can_be_reviewed
perms['submission.edit_review'] = can_be_reviewed & is_review_author
#perms['submission.view_reviews'] = has_reviewer_access | can_change_submissions
perms['submission.edit_speaker_list'] = is_speaker | can_change_submissions
#perms['submission.view_feedback'] = is_speaker | can_change_submissions | has_reviewer_access

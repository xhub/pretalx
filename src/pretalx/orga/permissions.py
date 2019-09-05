from datetime import timedelta

from bridgekeeper import perms
from bridgekeeper.rules import R, is_authenticated
from django.utils.timezone import now

from pretalx.person.permissions import (
    can_change_submissions, is_administrator, is_reviewer,
)
from pretalx.submission.permissions import (
    can_be_reviewed, can_view_all_reviews, can_view_reviews,
    is_review_author, reviewer_can_change_submissions,
)

can_change_event_settings = is_administrator | (
    is_authenticated & R(organiser__teams=R(members__in=lambda user: [user], can_change_event_settings=True))
)
can_change_organiser_settings = is_administrator | (
    is_authenticated & R(organiser__teams=R(members__in=lambda user: [user], can_change_organiser_settings=True))
)

can_change_any_organiser_settings = is_administrator | (is_authenticated & R(teams__can_change_organiser_settings=True))
can_create_events = is_administrator | (is_authenticated & R(teams__can_create_events=True))


# @rules.predicate
def can_change_teams(user, obj):  # TODO: this takes different classes currently
    from pretalx.event.models import Organiser, Team

    if isinstance(obj, Team):
        obj = obj.organiser
    if isinstance(obj, Organiser):
        return user.teams.filter(organiser=obj, can_change_teams=True).exists()
    event = getattr(obj, 'event', None)
    if not user or user.is_anonymous or not obj or not event:
        return False
    return user.is_administrator or event.teams.filter(members__in=[user], can_change_teams=True).exists()


reviews_are_open = R(review_phases__is_active=True, review_phases__can_review=True)  # TODO: this needs to be an AND
can_edit_mail = R(sent__isnull=True)
can_mark_speakers_arrived = R(date_to__gt=now().date(), date_from__lt=(now() + timedelta(days=1)).date())  # TODO: use of now
is_event_over = R(date_to__lt=now().date())  # TODO: use of now
reviews_are_open = R(review_phases__is_active=True, review_phases__can_see_speaker_names=True)  # TODO: this needs to be an AND
can_view_speaker_names = R(review_phases=R(is_active=True, can_see_speaker_names=True))


perms['orga.view_orga_area'] = can_change_submissions | is_reviewer
perms['orga.change_settings'] = can_change_event_settings
perms['orga.change_organiser_settings'] = can_change_organiser_settings
perms['orga.view_organisers'] = can_change_any_organiser_settings
#perms['orga.change_teams'] = is_administrator | can_change_teams
perms['orga.view_submission_cards'] = can_change_submissions
perms['orga.edit_cfp'] = can_change_event_settings
perms['orga.view_question'] = can_change_submissions
perms['orga.edit_question'] = can_change_event_settings
perms['orga.remove_question'] = can_change_event_settings
perms['orga.view_submission_type'] = can_change_submissions
perms['orga.edit_submission_type'] = can_change_event_settings
perms['orga.remove_submission_type'] = can_change_event_settings
perms['orga.view_tracks'] = can_change_submissions
perms['orga.view_track'] = can_change_submissions
perms['orga.edit_track'] = can_change_event_settings
perms['orga.remove_track'] = can_change_event_settings
perms['orga.view_mails'] = can_change_submissions
perms['orga.send_mails'] = can_change_submissions
perms['orga.edit_mails'] = can_change_submissions & can_edit_mail
perms['orga.purge_mails'] = can_change_submissions
perms['orga.view_mail_templates'] = can_change_submissions
perms['orga.edit_mail_templates'] = can_change_submissions
perms['orga.view_review_dashboard'] = can_change_submissions | is_reviewer
perms['orga.view_reviews'] = can_change_submissions | (is_reviewer & can_view_reviews)
perms['orga.view_all_reviews'] = can_change_submissions | (is_reviewer & can_view_all_reviews)
perms['orga.perform_reviews'] = is_reviewer & reviews_are_open
perms['orga.remove_review'] = is_administrator | (is_review_author & can_be_reviewed)
perms['orga.view_schedule'] = can_change_submissions
perms['orga.release_schedule'] = can_change_submissions
perms['orga.edit_schedule'] = can_change_submissions
perms['orga.schedule_talk'] = can_change_submissions
perms['orga.view_room'] = can_change_submissions
perms['orga.edit_room'] = can_change_submissions
perms['orga.view_speakers'] = can_change_submissions | (is_reviewer & can_view_speaker_names)
perms['orga.view_speaker'] = can_change_submissions | (is_reviewer & can_view_speaker_names)
perms['orga.change_speaker'] = can_change_submissions
perms['orga.view_submissions'] = can_change_submissions | is_reviewer
perms['orga.create_submission'] = can_change_submissions
perms['orga.change_submissions'] = can_change_submissions
perms['orga.change_submission_state'] = can_change_submissions | (is_reviewer & reviewer_can_change_submissions)
perms['orga.view_information'] = can_change_submissions
perms['orga.change_information'] = can_change_event_settings
perms['orga.create_events'] = can_create_events
perms['orga.change_plugins'] = is_administrator
perms['orga.mark_speakers_arrived'] = can_change_submissions & can_mark_speakers_arrived
perms['orga.see_speakers_arrival'] = can_change_submissions & is_event_over

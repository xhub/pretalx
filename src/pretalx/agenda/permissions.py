from bridgekeeper import perms
from bridgekeeper.rules import R

from pretalx.person.permissions import can_change_submissions

is_public = R(is_public=True)
has_agenda = R(schedules__published__isnull=False)
is_agenda_visible = is_public & R(_settings_objects=R(key='show_schedule', value='True'))
is_sneak_peek_visible = is_public & R(_settings_objects=R(key='show_sneak_peek', value='True'))
is_feedback_ready = R(does_accept_feedback=True)

is_current_schedule = R()
is_submission_visible = R(
    event=is_agenda_visible,
    slots=R(schedule=is_current_schedule, is_visible=True)  # TODO bridgekeeper: get current schedule. db field?
)
is_speaker_viewable = R(
    event=is_agenda_visible,
    user__submissions__slots=R(schedule=is_current_schedule, is_visible=True),
)


perms['agenda.view_schedule'] = (has_agenda & is_agenda_visible) | can_change_submissions
# perms['agenda.view_sneak_peek'] = ((~is_agenda_visible | ~has_agenda) & is_sneak_peek_visible) | can_change_submissions  # TODO bridgekeeper: TypeError: bad operand type for unary ~: 'And'
perms['agenda.view_slot'] = is_submission_visible | can_change_submissions
perms['agenda.view_speaker'] = is_speaker_viewable | can_change_submissions
perms['agenda.give_feedback'] = is_submission_visible & is_feedback_ready

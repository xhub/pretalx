import pytest
from django_scopes import scope, scopes_disabled
from hypothesis import given, settings, Verbosity
from hypothesis.extra.django import TestCase, from_model
from hypothesis.strategies import just

from pretalx.api.serializers.event import EventSerializer
from pretalx.api.serializers.question import AnswerSerializer, QuestionSerializer
from pretalx.api.serializers.review import ReviewSerializer
from pretalx.api.serializers.room import RoomOrgaSerializer, RoomSerializer
from pretalx.api.serializers.speaker import (
    SpeakerOrgaSerializer, SpeakerSerializer, SubmitterSerializer,
)
from pretalx.api.serializers.submission import (
    SubmissionOrgaSerializer, SubmissionSerializer,
)
from pretalx.event.models import Event
from pretalx.submission.models import Answer, Question, Submission


event_defaults = {
    value: just(None)
    for value in ['accept_template', 'ack_template', 'reject_template', 'update_template', 'question_template', 'plugins']
}


def prefix(data, prefix='event'):
    return {
        f'{prefix}__{key}': value
        for key, value in data.items()
    }


class TestSerializers(TestCase):

    @scopes_disabled()
    @given(event=from_model(Event, **event_defaults, __save=False))
    def test_event_serializer(self, event):
        data = EventSerializer(event).data
        assert data == {
            'name': event.name,
            'slug': event.slug,
            'is_public': event.is_public,
            'date_from': event.date_from.isoformat(),
            'date_to': event.date_to.isoformat(),
            'timezone': event.timezone,
            'urls': {
                key: getattr(event.urls, key).full()
                for key in ['base', 'schedule', 'login', 'feed']
            },
        }

    @scopes_disabled()
    @given(answer=from_model(
        Answer,
        __save=False,
        __infer_related_fields=True,
        submission=from_model(Submission, **prefix(event_defaults)),
        **prefix(event_defaults, 'question__event')
    ))
    def test_answer_serializer(self, answer):
        with scope(event=answer.question.event):
            data = AnswerSerializer(answer).data
            assert data == {
                'id': answer.id,
                'question': QuestionSerializer(answer.question).data,
                'answer': answer.answer,
                'answer_file': answer.answer_file.url if answer.answer_file else None,
                'submission': answer.submission.code if answer.submission else None,
                'person': None,  # TODO: get answer.person to work
                'options': [option.answer for option in answer.options.all()],
            }

    @scopes_disabled()
    @given(question=from_model(
        Question,
        __save=False,
        __infer_related_fields=True,
        **prefix(event_defaults),
    ))
    def test_question_serializer(self, question):
        with scope(event=question.event):
            data = QuestionSerializer(question).data
            assert data == {
                'id': question.id,
                'question': question.question,
                'required': question.required,
                'target': question.target,
                'options': [option.answer for option in question.options.all()]
            }


@pytest.mark.django_db
def test_submitter_serializer(submission):
    user = submission.speakers.first()
    data = SubmitterSerializer(user, context={'event': submission.event}).data
    assert data.keys() == {'name', 'code', 'biography', 'avatar'}
    assert data['name'] == user.name
    assert data['code'] == user.code


@pytest.mark.django_db
def test_submitter_serializer_without_profile(submission):
    with scope(event=submission.event):
        user = submission.speakers.first()
        user.profiles.all().delete()
        data = SubmitterSerializer(user, context={'event': submission.event}).data
    assert data.keys() == {'name', 'code', 'biography', 'avatar'}
    assert data['name'] == user.name
    assert data['code'] == user.code
    assert data['biography'] == ''


@pytest.mark.django_db
def test_speaker_serializer(slot):
    with scope(event=slot.submission.event):
        user_profile = slot.submission.speakers.first().profiles.first()
        user = user_profile.user
        data = SpeakerSerializer(user_profile).data
        assert slot.submission.code in data['submissions']
    assert data.keys() == {'name', 'code', 'biography', 'submissions', 'avatar'}
    assert data['name'] == user.name
    assert data['code'] == user.code


@pytest.mark.django_db
def test_speaker_orga_serializer(slot):
    with scope(event=slot.submission.event):
        user_profile = slot.submission.speakers.first().profiles.first()
        user = user_profile.user
        data = SpeakerOrgaSerializer(user_profile).data
    assert data.keys() == {
        'name',
        'code',
        'biography',
        'submissions',
        'avatar',
        'answers',
        'email',
        'availabilities',
    }
    assert data['name'] == user.name
    assert data['code'] == user.code
    assert data['email'] == user.email
    assert slot.submission.code in data['submissions']


@pytest.mark.django_db
def test_submission_serializer_for_organiser(submission, orga_user):
    class Request:
        user = orga_user
        event = submission.event
    with scope(event=submission.event):
        data = SubmissionOrgaSerializer(submission, context={'event': submission.event, 'request': Request()}).data
        assert set(data.keys()) == {
            'code',
            'speakers',
            'title',
            'submission_type',
            'state',
            'abstract',
            'description',
            'duration',
            'slot_count',
            'do_not_record',
            'is_featured',
            'content_locale',
            'slot',
            'image',
            'answers',
            'track',
            'notes',
            'internal_notes',
            'created',
        }
        assert isinstance(data['speakers'], list)
        assert data['speakers'][0] == {
            'name': submission.speakers.first().name,
            'code': submission.speakers.first().code,
            'biography': submission.speakers.first().event_profile(submission.event).biography,
            'avatar': None,
        }
        assert data['submission_type'] == str(submission.submission_type.name)
        assert data['slot'] is None
        assert data['created'] == submission.created.astimezone(submission.event.tz).isoformat()


@pytest.mark.django_db
def test_submission_serializer(submission):
    with scope(event=submission.event):
        data = SubmissionSerializer(submission, context={'event': submission.event}).data
        assert set(data.keys()) == {
            'code',
            'speakers',
            'title',
            'submission_type',
            'state',
            'abstract',
            'description',
            'duration',
            'slot_count',
            'do_not_record',
            'is_featured',
            'content_locale',
            'slot',
            'image',
            'track',
        }
        assert isinstance(data['speakers'], list)
        assert data['speakers'] == []
        assert data['submission_type'] == str(submission.submission_type.name)
        assert data['slot'] is None


@pytest.mark.django_db
def test_submission_slot_serializer(slot):
    with scope(event=slot.submission.event):
        data = SubmissionSerializer(
            slot.submission, context={'event': slot.submission.event}
        ).data
        assert set(data.keys()) == {
            'code',
            'speakers',
            'title',
            'submission_type',
            'state',
            'abstract',
            'description',
            'duration',
            'slot_count',
            'do_not_record',
            'is_featured',
            'content_locale',
            'slot',
            'image',
            'track',
        }
        assert set(data['slot'].keys()) == {'start', 'end', 'room'}
        assert data['slot']['room'] == slot.room.name


@pytest.mark.django_db
def test_review_serializer(review):
    with scope(event=review.event):
        data = ReviewSerializer(review).data
        assert set(data.keys()) == {
            'id',
            'answers',
            'submission',
            'user',
            'text',
            'score',
            'override_vote',
            'created',
            'updated',
        }
        assert data['submission'] == review.submission.code
        assert data['user'] == review.user.name
        assert data['answers'] == []


@pytest.mark.django_db
def test_room_serializer(room):
    data = RoomSerializer(room).data
    assert set(data.keys()) == {'id', 'name', 'description', 'capacity', 'position', 'url'}
    assert data['id'] == room.pk


@pytest.mark.django_db
def test_room_orga_serializer(room):
    with scope(event=room.event):
        data = RoomOrgaSerializer(room).data
        assert set(data.keys()) == {
            'id',
            'name',
            'description',
            'capacity',
            'position',
            'speaker_info',
            'availabilities',
            'url',
        }
        assert data['id'] == room.pk

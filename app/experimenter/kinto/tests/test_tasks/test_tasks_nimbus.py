import datetime

import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import (
    NimbusBucketRange,
    NimbusChangeLog,
    NimbusExperiment,
)
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.kinto import tasks
from experimenter.kinto.client import KINTO_REJECTED_STATUS
from experimenter.kinto.tests.mixins import MockKintoClientMixin


class TestPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )

    def test_push_experiment_to_kinto_sends_experiment_data(self):
        tasks.nimbus_push_experiment_to_kinto(self.experiment.id)

        data = NimbusExperimentSerializer(self.experiment).data

        self.assertTrue(
            NimbusBucketRange.objects.filter(experiment=self.experiment).exists()
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION_NIMBUS,
            bucket=settings.KINTO_BUCKET,
            if_not_exists=True,
        )

        self.assertTrue(
            NimbusChangeLog.objects.filter(
                experiment=self.experiment,
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                new_status=NimbusExperiment.Status.ACCEPTED,
            ).exists()
        )

    def test_push_experiment_to_kinto_reraises_exception(self):
        self.mock_kinto_client.create_record.side_effect = Exception

        with self.assertRaises(Exception):
            tasks.nimbus_push_experiment_to_kinto(self.experiment.id)


class TestCheckKintoPushQueue(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        mock_push_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_push_experiment_to_kinto.delay"
        )
        self.mock_push_task = mock_push_task_patcher.start()
        self.addCleanup(mock_push_task_patcher.stop)

    def test_check_with_empty_queue_pushes_nothing(self):
        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_check_experiment_with_no_review_status_pushes_nothing(self):
        for status in [
            NimbusExperiment.Status.DRAFT,
            NimbusExperiment.Status.ACCEPTED,
            NimbusExperiment.Status.LIVE,
            NimbusExperiment.Status.COMPLETE,
        ]:
            NimbusExperimentFactory.create(status=status)

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_check_experiment_with_review_and_kinto_pending_pushes_nothing(self):
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.REVIEW,
        )
        self.setup_kinto_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_not_called()

    def test_checkexperiment_with_review_and_no_kinto_pending_pushes_experiment(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW
        )
        self.assertEqual(experiment.changes.count(), 2)

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_called_with(experiment.id)

    def test_check_with_reject_review(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
        )

        self.mock_kinto_client.delete_record.return_value = {}
        self.mock_kinto_client.get_collection.side_effect = [
            {
                "data": {
                    "status": KINTO_REJECTED_STATUS,
                    "last_reviewer_comment": "it's no good",
                }
            },
            {"data": {"status": "anything"}},
        ]
        self.mock_kinto_client.get_records.side_effect = [
            [{"id": "another-experiment"}],
            [
                {"id": "another-experiment"},
                {"id": experiment.slug},
            ],
        ]
        tasks.nimbus_check_kinto_push_queue()

        self.mock_kinto_client.delete_record.assert_called()

        self.assertTrue(
            experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.ACCEPTED,
                new_status=NimbusExperiment.Status.DRAFT,
            ).exists()
        )


class TestCheckExperimentIsLive(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
        )

        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
        )

        experiment3 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )

        self.assertEqual(experiment1.changes.count(), 3)
        self.assertEqual(experiment2.changes.count(), 3)
        self.assertEqual(experiment3.changes.count(), 1)

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_live()

        self.assertEqual(experiment3.changes.count(), 1)

        self.assertTrue(
            experiment1.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.ACCEPTED,
                new_status=NimbusExperiment.Status.LIVE,
            ).exists()
        )

        self.assertFalse(
            experiment2.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.ACCEPTED,
                new_status=NimbusExperiment.Status.LIVE,
            ).exists()
        )


class TestCheckExperimentIsComplete(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_not_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
        )

        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
        )

        experiment3 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )

        self.assertEqual(experiment1.changes.count(), 4)
        self.assertEqual(experiment2.changes.count(), 4)
        self.assertEqual(experiment3.changes.count(), 1)

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_complete()

        self.assertEqual(experiment3.changes.count(), 1)

        self.assertFalse(
            experiment1.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                new_status=NimbusExperiment.Status.COMPLETE,
            ).exists()
        )

        self.assertTrue(
            experiment2.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                new_status=NimbusExperiment.Status.COMPLETE,
            ).exists()
        )

    def test_experiment_ending_email_not_sent_for_experiments_before_proposed_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        self.assertEqual(experiment.emails.count(), 0)
        self.setup_kinto_get_main_records([experiment.slug])
        tasks.nimbus_check_experiments_are_complete()
        self.assertEqual(experiment.emails.count(), 0)

    def test_experiment_ending_email_sent_for_experiments_past_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))

        self.assertEqual(experiment.emails.count(), 0)

        self.setup_kinto_get_main_records([experiment.slug])
        tasks.nimbus_check_experiments_are_complete()

        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.EXPERIMENT_END
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

from smtplib import SMTPException

import markus
import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase
from markus.testing import MetricsMock
from requests.exceptions import RequestException

from experimenter.experiments import bugzilla, tasks
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import (
    MockBugzillaMixin,
    MockNormandyMixin,
    MockRequestMixin,
)
from experimenter.notifications.models import Notification


class TestSendReviewEmailTask(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )

    def test_successful_email_creates_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.send_review_email_task(
                self.user.id,
                self.experiment.name,
                self.experiment.experiment_url,
                False,
            )

            # We should get 3 stats calls firing in order of completion.
            self.assertEqual(len(mm.get_records()), 3)
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.send_review_email.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.send_review_email.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING, "experiments.tasks.send_review_email.timing"
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR, "experiments.tasks.send_review_email.failed"
                )
            )

        self.assertEqual(len(mail.outbox), 1)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_REVIEW_EMAIL.format(
                email=settings.EMAIL_REVIEW, name=self.experiment.name
            ),
        )

    def test_failed_email_doesnt_create_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        with mock.patch(
            "experimenter.experiments.tasks.send_review_email_task"
        ) as mocked:
            mocked.side_effect = SMTPException
            with self.assertRaises(SMTPException):
                with MetricsMock() as mm:
                    tasks.send_review_email_task(
                        self.user.id,
                        self.experiment.name,
                        self.experiment.experiment_url,
                        False,
                    )

                    self.assertTrue(
                        mm.has_record(
                            markus.INCR,
                            "experiments.tasks.send_review_email.started",
                            value=1,
                        )
                    )
                    self.assertTrue(
                        mm.has_record(
                            markus.INCR,
                            "experiments.tasks.send_review_email.failed",
                            value=1,
                        )
                    )
                    # Failures should abort timing metrics.
                    self.assertFalse(
                        mm.has_record(
                            markus.TIMING,
                            "experiments.tasks.send_review_email.timing",
                        )
                    )
                    # Completed should not be sent.
                    self.assertFalse(
                        mm.has_record(
                            markus.INCR,
                            "experiments.tasks.send_review_email.completed",
                        )
                    )

        self.assertEqual(Notification.objects.count(), 0)


class TestCreateBugTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, bugzilla_id=None
        )

    def test_experiment_bug_successfully_created(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.create_experiment_bug_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.create_experiment_bug.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.failed",
                )
            )

        self.mock_bugzilla_requests_post.assert_called()

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, self.bugzilla_id)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_CREATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_creates_error_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.create_experiment_bug_task(
                    self.user.id, self.experiment.id
                )

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.started",
                        value=1,
                    )
                )
                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.failed",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.TIMING,
                        "experiments.tasks.create_experiment_bug.timing",
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.completed",
                    )
                )

        self.mock_bugzilla_requests_post.assert_called()
        self.assertEqual(Notification.objects.count(), 1)

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, None)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message, tasks.NOTIFICATION_MESSAGE_CREATE_BUG_FAILED
        )


class TestUpdateTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        self.experiment.bugzilla_id = self.bugzilla_id
        self.experiment.save()

    def test_experiment_bug_successfully_updated(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.update_experiment_bug_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.update_experiment_bug.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.failed",
                )
            )

        self.mock_bugzilla_requests_put.assert_called()

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_ADD_COMMENT.format(
                bug_url=self.experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_doesnt_create_notifications(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_put.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.update_experiment_bug_task(
                    self.user.id, self.experiment.id
                )

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.started",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.timing",
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.completed",
                    )
                )
        self.mock_bugzilla_requests_put.assert_called()
        self.assertEqual(Notification.objects.count(), 0)

    def test_internal_only_does_not_update_bugzilla(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, risk_internal_only=True
        )

        with MetricsMock() as mm:
            tasks.update_experiment_bug_task(self.user.id, experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.started",
                    value=1,
                )
            )
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiements.tasks.update_experiment_bug.completed",
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.update_experiment_bug.timing",
                )
            )

            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "expeiments.tasks.update_experiement_bug.failed",
                )
            )

        self.mock_bugzilla_requests_put.assert_not_called()

        self.assertEqual(Notification.objects.count(), 0)


class TestUpdateExperimentStatus(
    MockRequestMixin, MockNormandyMixin, TestCase
):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1234
        )

    def test_successful_experiment_status_update(self):
        with MetricsMock() as mm:
            tasks.update_experiment_status()
            self.assertEqual(len(mm.get_records()), 4)
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_status.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_status.updated",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_status.completed",
                    value=1,
                )
            )

    def test_experiement_status_update_with_failure(self):
        self.mock_normandy_requests_get.side_effect = RequestException()
        with MetricsMock() as mm:
            tasks.update_experiment_status()
            self.assertEqual(len(mm.get_records()), 4)
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_status.started",
                    value=1,
                )
            )
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiement_status.updated",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_status.failed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_status.completed",
                    value=1,
                )
            )

    def test_accepted_experiment_becomes_live_if_normandy_enabled(self):
        tasks.update_experiment_status()
        experiment = Experiment.objects.get(normandy_id=1234)
        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertTrue(
            experiment.changes.filter(
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_accepted_experiment_stays_accepted_if_normandy_disabled(self):

        self.mock_normandy_requests_get.return_value = (
            self.buildMockSuccessDisabledResponse()
        )
        experiment = Experiment.objects.get(normandy_id=1234)
        tasks.update_experiment_status()
        self.assertFalse(
            experiment.changes.filter(
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

    def test_live_experiment_stays_live_if_normandy_enabled(self):
        experiment = Experiment.objects.get(normandy_id=1234)
        experiment.status = Experiment.STATUS_LIVE
        tasks.update_experiment_status()
        self.assertEqual(experiment.status, Experiment.STATUS_LIVE)
        self.assertFalse(
            experiment.changes.filter(
                old_status=Experiment.STATUS_LIVE,
                new_status=Experiment.STATUS_COMPLETE,
            ).exists()
        )

    def test_live_experiment_becomes_complete_if_normandy_disabled(self):

        self.mock_normandy_requests_get.return_value = (
            self.buildMockSuccessDisabledResponse()
        )
        experiment = Experiment.objects.get(normandy_id=1234)
        experiment.status = Experiment.STATUS_LIVE
        experiment.save()
        tasks.update_experiment_status()
        self.assertTrue(
            experiment.changes.filter(
                old_status=Experiment.STATUS_LIVE,
                new_status=Experiment.STATUS_COMPLETE,
            ).exists()
        )

    def test_one_failure_does_not_affect_other_experiment_status_updates(self):
        self.setUpMockNormandyFailWhenIdIs1234()
        self.experiment2 = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED, normandy_id=1235
        )

        tasks.update_experiment_status()
        self.assertFalse(
            self.experiment.changes.filter(
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )
        self.assertTrue(
            self.experiment2.changes.filter(
                old_status=Experiment.STATUS_ACCEPTED,
                new_status=Experiment.STATUS_LIVE,
            ).exists()
        )

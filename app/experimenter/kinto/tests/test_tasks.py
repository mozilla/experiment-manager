import mock
from datetime import datetime
from django.conf import settings
from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.kinto.tests.mixins import MockKintoClientMixin
from experimenter.kinto import tasks
from experimenter.kinto.serializers import ExperimentRapidRecipeSerializer


class TestPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

    def test_push_experiment_to_kinto_sends_experiment_data(self):
        today = datetime.today().isoformat()
        mock_module = "experimenter.kinto.serializers"

        mock_method = "{}.ExperimentRapidArgumentSerializer.get_startDate".format(
            mock_module
        )
        mock_serialize_start_date_patcher = mock.patch(mock_method)
        mock_serialize_start_date = mock_serialize_start_date_patcher.start()
        mock_serialize_start_date = mock.Mock()
        mock_serialize_start_date.return_value = today
        self.addCleanup(mock_serialize_start_date_patcher.stop)
        tasks.push_experiment_to_kinto(self.experiment.id)

        data = ExperimentRapidRecipeSerializer(self.experiment).data

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION,
            bucket=settings.KINTO_BUCKET,
            if_not_exists=True,
        )

    def test_push_experiment_to_kinto_reraises_exception(self):
        self.mock_kinto_client.create_record.side_effect = Exception

        with self.assertRaises(Exception):
            tasks.push_experiment_to_kinto(self.experiment.id)

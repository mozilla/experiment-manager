import logging
from datetime import datetime, timezone, timedelta

from django.utils.text import slugify
from django.conf import settings
from django.core.management.base import BaseCommand
from stmoab.ExperimentDashboard import ExperimentDashboard

from experimenter.experiments.models import Experiment, ExperimentChangeLog


def sanitize_name(name):
    return slugify(name).replace('-', ' ').title()


DASHBOARD_TAG_NAME = 'Experimenter Dashboard'


class Command(BaseCommand):
    POPULATION_TEMPLATE = 'UT Experiment Template: Population Size'
    EXISTING_USERS_SCALARS_TEMPLATE = (
        "Experiment Template Rate Scalars: [Existing Users]")
    EXISTING_USERS_MAPS_TEMPLATE = (
        "Experiment Template Rate Maps: [Existing Users]")
    NEW_USERS_SCALARS_TEMPLATE = (
        "Experiment Template Rate Scalars: [New Users]")
    NEW_USERS_MAPS_TEMPLATE = "Experiment Template Rate Maps: [New Users]"
    EVENTS_PER_HOUR_TEMPLATE = 'TTests Template Per Hour UT Five:'
    UT_HOURLY_TTABLE = 'Statistical Analysis (Per Active Hour) - UT'
    help = 'Generates Redash dashboards'

    def generate_dashboards(self):
        recent_changelog_complete = ExperimentChangeLog.objects.filter(
            old_status=Experiment.STATUS_LIVE,
            new_status=Experiment.STATUS_COMPLETE).filter(
            changed_on__gte=(datetime.now(timezone.utc) - timedelta(days=3)))

        recently_ended_experiments = Experiment.objects.filter(
            status=Experiment.STATUS_COMPLETE).filter(
            changes__in=recent_changelog_complete)

        in_flight_experiments = Experiment.objects.filter(
            status=Experiment.STATUS_LIVE
        )

        missing_dashboard_experiments = Experiment.objects.filter(
            dashboard_url__isnull=True)
        relevant_experiments = (
            recently_ended_experiments |
            missing_dashboard_experiments |
            in_flight_experiments).distinct()

        for exp in relevant_experiments:
            end_date = (None
                        if exp.end_date is None
                        else exp.end_date.strftime("%Y-%m-%d"))
            try:
                dash = ExperimentDashboard(
                  settings.REDASH_API_KEY,
                  DASHBOARD_TAG_NAME,
                  sanitize_name(exp.name),
                  exp.slug,
                  exp.start_date.strftime("%Y-%m-%d"),
                  end_date
                )

                # This dashboard was recently updated, no need to update again.
                update_begin = dash.get_update_range().get("min", None)
                if update_begin is not None and (
                  update_begin > (datetime.now() - timedelta(days=1))):
                    continue

                dash.add_graph_templates(self.POPULATION_TEMPLATE)

                # Existing Users
                dash.add_graph_templates(
                    self.EXISTING_USERS_SCALARS_TEMPLATE,
                    dash.UT_HOURLY_EVENTS
                )
                dash.add_graph_templates(
                    self.EXISTING_USERS_MAPS_TEMPLATE,
                    dash.MAPPED_UT_EVENTS
                )

                # New Users
                dash.add_graph_templates(
                    self.NEW_USERS_SCALARS_TEMPLATE, dash.UT_HOURLY_EVENTS)
                dash.add_graph_templates(
                    self.NEW_USERS_MAPS_TEMPLATE, dash.MAPPED_UT_EVENTS)

                exp.dashboard_url = dash.public_url
                exp.save()
            except ExperimentDashboard.ExternalAPIError as external_api_err:
                logging.error((
                  'ExternalAPIError '
                  'for {experiment}: {err}').format(
                  experiment=exp, err=external_api_err))
            except ValueError as val_err:
                logging.error((
                  'ExperimentDashboard Value Error '
                  'for {experiment}: {err}').format(
                  experiment=exp, err=val_err))

    def handle(self, *args, **options):
        self.generate_dashboards()

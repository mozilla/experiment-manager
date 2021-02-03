import json

from django.conf import settings
from rest_framework import serializers

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBucketRange,
    NimbusExperiment,
    NimbusProbe,
    NimbusProbeSet,
)


class NimbusBucketRangeSerializer(serializers.ModelSerializer):
    randomizationUnit = serializers.ReadOnlyField(
        source="isolation_group.randomization_unit"
    )
    namespace = serializers.ReadOnlyField(source="isolation_group.namespace")
    total = serializers.ReadOnlyField(source="isolation_group.total")

    class Meta:
        model = NimbusBucketRange
        fields = (
            "randomizationUnit",
            "namespace",
            "start",
            "count",
            "total",
        )


class NimbusBranchSerializer(serializers.ModelSerializer):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = NimbusBranch
        fields = ("slug", "ratio", "feature")

    def to_representation(self, branch):
        data = super().to_representation(branch)
        if not branch.experiment.feature_config:
            data = {k: v for k, v in data.items() if k != "feature"}
        return data

    def get_feature(self, obj):
        if obj.experiment.feature_config:
            return {
                "featureId": obj.experiment.feature_config.slug,
                "enabled": obj.feature_enabled,
                "value": json.loads(obj.feature_value) if obj.feature_value else None,
            }


class NimbusExperimentSerializer(serializers.ModelSerializer):
    schemaVersion = serializers.ReadOnlyField(default=settings.NIMBUS_SCHEMA_VERSION)
    id = serializers.ReadOnlyField(source="slug")
    arguments = serializers.ReadOnlyField(default={})
    application = serializers.SerializerMethodField()
    appName = serializers.SerializerMethodField()
    appId = serializers.SerializerMethodField()
    userFacingName = serializers.ReadOnlyField(source="name")
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    isEnrollmentPaused = serializers.ReadOnlyField(source="is_paused")
    bucketConfig = NimbusBucketRangeSerializer(source="bucket_range")
    probeSets = serializers.SerializerMethodField()
    branches = NimbusBranchSerializer(many=True)
    targeting = serializers.SerializerMethodField()
    startDate = serializers.DateTimeField(source="start_date")
    endDate = serializers.DateTimeField(source="end_date")
    proposedDuration = serializers.ReadOnlyField(source="proposed_duration")
    proposedEnrollment = serializers.ReadOnlyField(source="proposed_enrollment")
    referenceBranch = serializers.SerializerMethodField()
    featureIds = serializers.SerializerMethodField()

    class Meta:
        model = NimbusExperiment
        fields = (
            "schemaVersion",
            "slug",
            "id",
            "arguments",
            "application",
            "appName",
            "appId",
            "channel",
            "userFacingName",
            "userFacingDescription",
            "isEnrollmentPaused",
            "bucketConfig",
            "probeSets",
            "branches",
            "targeting",
            "startDate",
            "endDate",
            "proposedDuration",
            "proposedEnrollment",
            "referenceBranch",
            "featureIds",
        )

    def get_application(self, obj):
        return self.get_appId(obj)

    def get_appName(self, obj):
        if obj.is_desktop_experiment:
            return obj.FIREFOX_DESKTOP_APP_NAME
        return str(obj.application)

    def get_appId(self, obj):
        if obj.is_fenix_experiment:
            if obj.channel in NimbusExperiment.CHANNEL_FENIX_APP_ID:
                return str(NimbusExperiment.CHANNEL_FENIX_APP_ID[obj.channel])
            return ""
        return str(obj.application)

    def get_probeSets(self, obj):
        return list(obj.probe_sets.all().order_by("slug").values_list("slug", flat=True))

    def get_referenceBranch(self, obj):
        if obj.reference_branch:
            return obj.reference_branch.slug

    def get_targeting(self, obj):
        exprs = []

        if obj.is_desktop_experiment:
            if obj.channel:
                exprs.append(
                    NimbusExperiment.TARGETING_CHANNEL.format(channel=obj.channel)
                )
            if obj.firefox_min_version:
                exprs.append(
                    NimbusExperiment.TARGETING_VERSION.format(
                        version=obj.firefox_min_version
                    )
                )

        if obj.targeting_config:
            exprs.append(obj.targeting_config.targeting.format(experiment=obj))

        # TODO: Remove opt-out after Firefox 84 is the earliest supported Desktop
        if obj.is_desktop_experiment:
            exprs.append("'app.shield.optoutstudies.enabled'|preferenceValue")

        return " && ".join(exprs)

    def get_featureIds(self, obj):
        if obj.feature_config:
            return [obj.feature_config.slug]
        return []


class NimbusProbeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NimbusProbe
        fields = (
            "kind",
            "name",
            "event_category",
            "event_method",
            "event_object",
            "event_value",
        )


class NimbusProbeSetSerializer(serializers.ModelSerializer):
    probes = NimbusProbeSerializer(many=True)

    class Meta:
        model = NimbusProbeSet
        fields = ("name", "slug", "probes")


import json
from rest_framework import serializers

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    VariantPreferences,
)

from experimenter.experiments.serializers.entities import PrefTypeField


class VariantPrefValueField(serializers.Field):

    def to_representation(self, obj):
        pref_type = obj.experiment.pref_type
        if pref_type in (Experiment.PREF_TYPE_BOOL, Experiment.PREF_TYPE_INT):
            return json.loads(obj.value)

        return obj.value


class VariantPreferencePrefValueField(serializers.Field):

    def to_representation(self, obj):
        pref_type = obj.pref_type
        if pref_type in (Experiment.PREF_TYPE_BOOL, Experiment.PREF_TYPE_INT):
            return json.loads(obj.pref_value)
        return obj.pref_value


class FilterObjectBucketSampleSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    input = serializers.ReadOnlyField(default=["normandy.recipe.id", "normandy.userId"])
    start = serializers.ReadOnlyField(default=0)
    count = serializers.SerializerMethodField()
    total = serializers.ReadOnlyField(default=10000)

    class Meta:
        model = Experiment
        fields = ("type", "input", "start", "count", "total")

    def get_type(self, obj):
        return "bucketSample"

    def get_count(self, obj):
        return int(obj.population_percent * 100)


class FilterObjectChannelSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    channels = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "channels")

    def get_type(self, obj):
        return "channel"

    def get_channels(self, obj):
        return [obj.firefox_channel.lower()]


class FilterObjectVersionsSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "versions")

    def get_type(self, obj):
        return "version"

    def get_versions(self, obj):
        return obj.versions_integer_list


class FilterObjectLocaleSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    locales = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "locales")

    def get_type(self, obj):
        return "locale"

    def get_locales(self, obj):
        return list(obj.locales.all().values_list("code", flat=True))


class FilterObjectCountrySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "countries")

    def get_type(self, obj):
        return "country"

    def get_countries(self, obj):
        return list(obj.countries.all().values_list("code", flat=True))


class ExperimentRecipeVariantSerializer(serializers.ModelSerializer):
    value = VariantPrefValueField(source="*")

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "value")

    def get_value(self, obj):
        pref_type = obj.experiment.pref_type
        if pref_type in (Experiment.PREF_TYPE_BOOL, Experiment.PREF_TYPE_INT):
            return json.loads(obj.value)

        return obj.value


class ExperimentRecipeAddonVariantSerializer(serializers.ModelSerializer):
    extensionApiId = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "extensionApiId")

    def get_extensionApiId(self, obj):
        return None


class SingularPreferenceRecipeValueSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="experiment.pref_branch")
    preferenceType = PrefTypeField(source="experiment.pref_type")
    preferenceValue = VariantPrefValueField(source="*")

    class Meta:
        model = ExperimentVariant
        fields = ("preferenceBranchType", "preferenceType", "preferenceValue")


class VariantPreferenceRecipeListSerializer(serializers.ListSerializer):

    def to_representation(self, obj):
        experiment = obj.instance.experiment

        if experiment.is_multi_pref:
            serialized_data = super().to_representation(obj)
            return {entry.pop("pref_name"): entry for entry in serialized_data}

        else:
            preference_values = SingularPreferenceRecipeValueSerializer(obj.instance).data
            return {experiment.pref_key: preference_values}


class VariantPreferenceRecipeSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    preferenceType = PrefTypeField(source="pref_type")
    preferenceValue = VariantPreferencePrefValueField(source="*")

    class Meta:
        list_serializer_class = VariantPreferenceRecipeListSerializer
        model = VariantPreferences
        fields = (
            "preferenceBranchType",
            "preferenceType",
            "preferenceValue",
            "pref_name",
        )


class ExperimentRecipeMultiPrefVariantSerializer(serializers.ModelSerializer):
    preferences = VariantPreferenceRecipeSerializer(many=True)

    class Meta:
        model = ExperimentVariant
        fields = ("preferences", "ratio", "slug")


class ExperimentRecipePrefArgumentsSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    slug = serializers.ReadOnlyField(source="normandy_slug")
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")
    preferenceName = serializers.ReadOnlyField(source="pref_key")
    preferenceType = PrefTypeField(source="pref_type")
    branches = ExperimentRecipeVariantSerializer(many=True, source="variants")

    class Meta:
        model = Experiment
        fields = (
            "preferenceBranchType",
            "slug",
            "experimentDocumentUrl",
            "preferenceName",
            "preferenceType",
            "branches",
        )


class ExperimentRecipeBranchedArgumentsSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    userFacingName = userFacingDescription = serializers.ReadOnlyField(
        source="public_name"
    )
    userFacingDescription = serializers.ReadOnlyField(source="public_description")
    branches = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "userFacingName", "userFacingDescription")


class ExperimentRecipeBranchedAddonArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    branches = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "userFacingName", "userFacingDescription", "branches")

    def get_branches(self, obj):
        return ExperimentRecipeAddonVariantSerializer(obj.variants, many=True).data


class ExperimentRecipeMultiPrefArgumentsSerializer(
    ExperimentRecipeBranchedArgumentsSerializer
):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    branches = serializers.SerializerMethodField()
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")

    class Meta:
        model = Experiment
        fields = (
            "slug",
            "userFacingName",
            "userFacingDescription",
            "branches",
            "experimentDocumentUrl",
        )

    def get_branches(self, obj):
        return ExperimentRecipeMultiPrefVariantSerializer(obj.variants, many=True).data


class ExperimentRecipeAddonArgumentsSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="addon_experiment_id")
    description = serializers.ReadOnlyField(source="public_description")

    class Meta:
        model = Experiment
        fields = ("name", "description")


class ExperimentRecipeAddonRolloutArgumentsSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    extensionApiId = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "extensionApiId")

    def get_extensionApiId(self, obj):
        return f"TODO: {obj.addon_release_url}"


class ExperimentRecipePrefRolloutArgumentsSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField(source="normandy_slug")
    preferences = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("slug", "preferences")

    # FIX
    def get_value(self, obj):
        pref_type = obj.pref_type
        if pref_type in (Experiment.PREF_TYPE_BOOL, Experiment.PREF_TYPE_INT):
            return json.loads(obj.pref_value)

        return obj.pref_value

    def get_preferences(self, obj):
        return [{"preferenceName": obj.pref_key, "value": self.get_value(obj)}]


class ExperimentRecipeSerializer(serializers.ModelSerializer):
    action_name = serializers.SerializerMethodField()
    filter_object = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    arguments = serializers.SerializerMethodField()
    experimenter_slug = serializers.ReadOnlyField(source="slug")

    class Meta:
        model = Experiment
        fields = (
            "action_name",
            "name",
            "filter_object",
            "comment",
            "arguments",
            "experimenter_slug",
        )

    def get_action_name(self, obj):
        if obj.use_multi_pref_serializer:
            return "multi-preference-experiment"
        if obj.is_pref_experiment:
            return "preference-experiment"
        elif obj.use_branched_addon_serializer:
            return "branched-addon-study"
        elif obj.is_addon_experiment:
            return "opt-out-study"
        elif obj.is_addon_rollout:
            return "addon-rollout"
        elif obj.is_pref_rollout:
            return "preference-rollout"

    def get_filter_object(self, obj):
        filter_objects = [
            FilterObjectBucketSampleSerializer(obj).data,
            FilterObjectChannelSerializer(obj).data,
            FilterObjectVersionsSerializer(obj).data,
        ]

        if obj.locales.count():
            filter_objects.append(FilterObjectLocaleSerializer(obj).data)

        if obj.countries.count():
            filter_objects.append(FilterObjectCountrySerializer(obj).data)

        return filter_objects

    def get_arguments(self, obj):
        if obj.use_multi_pref_serializer:
            return ExperimentRecipeMultiPrefArgumentsSerializer(obj).data
        elif obj.is_pref_experiment:
            return ExperimentRecipePrefArgumentsSerializer(obj).data
        elif obj.use_branched_addon_serializer:
            return ExperimentRecipeBranchedAddonArgumentsSerializer(obj).data
        elif obj.is_addon_experiment:
            return ExperimentRecipeAddonArgumentsSerializer(obj).data
        elif obj.is_addon_rollout:
            return ExperimentRecipeAddonRolloutArgumentsSerializer(obj).data
        elif obj.is_pref_rollout:
            return ExperimentRecipePrefRolloutArgumentsSerializer(obj).data

    def get_comment(self, obj):
        return f"Platform: {obj.platform}\n{obj.client_matching}"

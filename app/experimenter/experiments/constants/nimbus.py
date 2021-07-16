from dataclasses import dataclass
from typing import Dict

from django.conf import settings
from django.db import models


class Channel(models.TextChoices):
    NO_CHANNEL = ""
    UNBRANDED = "default"
    NIGHTLY = "nightly"
    BETA = "beta"
    RELEASE = "release"


class BucketRandomizationUnit(models.TextChoices):
    NORMANDY = "normandy_id"
    NIMBUS = "nimbus_id"


@dataclass
class ApplicationConfig:
    name: str
    slug: str
    app_name: str
    channel_app_id: Dict[str, str]
    default_app_id: str
    rs_experiments_collection: str
    randomization_unit: str


APPLICATION_CONFIG_DESKTOP = ApplicationConfig(
    name="Firefox Desktop",
    slug="firefox-desktop",
    app_name="firefox_desktop",
    channel_app_id={
        Channel.NIGHTLY: "firefox-desktop",
        Channel.BETA: "firefox-desktop",
        Channel.RELEASE: "firefox-desktop",
    },
    default_app_id="firefox-desktop",
    rs_experiments_collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
    randomization_unit=BucketRandomizationUnit.NORMANDY,
)

APPLICATION_CONFIG_FENIX = ApplicationConfig(
    name="Firefox for Android (Fenix)",
    slug="fenix",
    app_name="fenix",
    channel_app_id={
        Channel.NIGHTLY: "org.mozilla.fenix",
        Channel.BETA: "org.mozilla.firefox_beta",
        Channel.RELEASE: "org.mozilla.firefox",
    },
    default_app_id="",
    rs_experiments_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)

APPLICATION_CONFIG_IOS = ApplicationConfig(
    name="Firefox for iOS",
    slug="ios",
    app_name="firefox_ios",
    channel_app_id={
        Channel.NIGHTLY: "org.mozilla.ios.Fennec",
        Channel.BETA: "org.mozilla.ios.FirefoxBeta",
        Channel.RELEASE: "org.mozilla.ios.Firefox",
    },
    default_app_id="",
    rs_experiments_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)


class Application(models.TextChoices):
    DESKTOP = (APPLICATION_CONFIG_DESKTOP.slug, APPLICATION_CONFIG_DESKTOP.name)
    FENIX = (APPLICATION_CONFIG_FENIX.slug, APPLICATION_CONFIG_FENIX.name)
    IOS = (APPLICATION_CONFIG_IOS.slug, APPLICATION_CONFIG_IOS.name)


@dataclass
class NimbusTargetingConfig:
    name: str
    slug: str
    description: str
    targeting: str
    desktop_telemetry: str
    application_choice_names: list[str]


TARGETING_NO_TARGETING = NimbusTargetingConfig(
    name="No Targeting",
    slug="",
    description="All users",
    targeting="",
    desktop_telemetry="",
    application_choice_names=(
        Application.DESKTOP.name,
        Application.FENIX.name,
        Application.IOS.name,
    ),
)

TARGETING_ALL_ENGLISH = NimbusTargetingConfig(
    name="All English users",
    slug="all_english",
    description="All users in en-* locales.",
    targeting="localeLanguageCode == 'en'",
    desktop_telemetry="STARTS_WITH(environment.settings.locale, 'en')",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_US_ONLY = NimbusTargetingConfig(
    name="US users (en)",
    slug="us_only",
    description="All users in the US with an en-* locale.",
    targeting="localeLanguageCode == 'en' && region == 'US'",
    desktop_telemetry=(
        "STARTS_WITH(environment.settings.locale, 'en') "
        "AND normalized_country_code = 'US'"
    ),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users (en)",
    slug="first_run",
    description=("First start-up users (e.g. for about:welcome) with an en-* " "locale."),
    targeting=("{en} && (({is_first_startup} && {not_see_aw}) || {sticky})").format(
        en=TARGETING_ALL_ENGLISH.targeting,
        is_first_startup="isFirstStartup",
        not_see_aw="!('trailhead.firstrun.didSeeAboutWelcome'|preferenceValue)",
        sticky="experiment.slug in activeExperiments",
    ),
    desktop_telemetry=(
        "STARTS_WITH(environment.settings.locale, 'en') "
        "AND payload.info.profile_subsession_counter = 1"
    ),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = NimbusTargetingConfig(
    name="First start-up users (en) from Chrome",
    slug="first_run_chrome",
    description=(
        "First start-up users (e.g. for about:welcome) who download Firefox "
        "from Chrome with an en-* locale."
    ),
    targeting=("{first_run} && attributionData.ua == 'chrome'").format(
        first_run=TARGETING_FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.settings.attribution.ua = 'chrome'"
    ).format(first_run=TARGETING_FIRST_RUN.desktop_telemetry),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_FIRST_RUN_WINDOWS_1903_NEWER = NimbusTargetingConfig(
    name="First start-up users (en) on Windows 10 1903 (build 18362) or newer",
    slug="first_run_win1903",
    description=(
        "First start-up users (e.g. for about:welcome) on Win 18362+ with an en-* locale."
    ),
    targeting=("{first_run} && os.windowsBuildNumber >= 18362").format(
        first_run=TARGETING_FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362"
    ).format(first_run=TARGETING_FIRST_RUN.desktop_telemetry),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_HOMEPAGE_GOOGLE = NimbusTargetingConfig(
    name="Homepage set to google.com",
    slug="homepage_google_dot_com",
    description="US users (en) with their Homepage set to google.com",
    targeting=(
        "localeLanguageCode == 'en' && "
        "region == 'US' && "
        "!homePageSettings.isDefault && "
        "homePageSettings.isCustomUrl && "
        "homePageSettings.urls[.host == 'google.com']|length > 0"
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_URLBAR_FIREFOX_SUGGEST = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) US users (en)",
    slug="urlbar_firefox_suggest_us_en",
    description="US (en) users with the default search suggestion showing order",
    targeting="{us_en} && {default_order}".format(
        us_en=TARGETING_US_ONLY.targeting,
        default_order="'browser.urlbar.showSearchSuggestionsFirst'|preferenceValue",
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)


class NimbusConstants(object):
    class Status(models.TextChoices):
        DRAFT = "Draft"
        PREVIEW = "Preview"
        LIVE = "Live"
        COMPLETE = "Complete"

    class PublishStatus(models.TextChoices):
        IDLE = "Idle"
        REVIEW = "Review"
        APPROVED = "Approved"
        WAITING = "Waiting"

    Application = Application

    VALID_STATUS_TRANSITIONS = {
        Status.DRAFT: (Status.PREVIEW,),
        Status.PREVIEW: (Status.DRAFT,),
    }
    STATUS_ALLOWS_UPDATE = (Status.DRAFT,)

    # Valid status_next values for given status values
    VALID_STATUS_NEXT_VALUES = {
        Status.DRAFT: (None, Status.LIVE),
        Status.PREVIEW: (None, Status.LIVE),
        Status.LIVE: (None, Status.LIVE, Status.COMPLETE),
    }

    VALID_PUBLISH_STATUS_TRANSITIONS = {
        PublishStatus.IDLE: (PublishStatus.REVIEW, PublishStatus.APPROVED),
        PublishStatus.REVIEW: (
            PublishStatus.IDLE,
            PublishStatus.APPROVED,
        ),
    }
    PUBLISH_STATUS_ALLOWS_UPDATE = (PublishStatus.IDLE,)

    STATUS_UPDATE_EXEMPT_FIELDS = (
        "status",
        "status_next",
        "publish_status",
    )

    APPLICATION_CONFIGS = {
        Application.DESKTOP: APPLICATION_CONFIG_DESKTOP,
        Application.FENIX: APPLICATION_CONFIG_FENIX,
        Application.IOS: APPLICATION_CONFIG_IOS,
    }

    Channel = Channel

    class DocumentationLink(models.TextChoices):
        DS_JIRA = "DS_JIRA", "Data Science Jira Ticket"
        DESIGN_DOC = "DESIGN_DOC", "Experiment Design Document"
        ENG_TICKET = "ENG_TICKET", "Engineering Ticket (Bugzilla/Jira/GitHub)"

    class Version(models.TextChoices):
        NO_VERSION = ""
        FIREFOX_11 = "11.!"
        FIREFOX_12 = "12.!"
        FIREFOX_13 = "13.!"
        FIREFOX_14 = "14.!"
        FIREFOX_15 = "15.!"
        FIREFOX_16 = "16.!"
        FIREFOX_17 = "17.!"
        FIREFOX_18 = "18.!"
        FIREFOX_19 = "19.!"
        FIREFOX_20 = "20.!"
        FIREFOX_21 = "21.!"
        FIREFOX_22 = "22.!"
        FIREFOX_23 = "23.!"
        FIREFOX_24 = "24.!"
        FIREFOX_25 = "25.!"
        FIREFOX_26 = "26.!"
        FIREFOX_27 = "27.!"
        FIREFOX_28 = "28.!"
        FIREFOX_29 = "29.!"
        FIREFOX_30 = "30.!"
        FIREFOX_31 = "31.!"
        FIREFOX_32 = "32.!"
        FIREFOX_33 = "33.!"
        FIREFOX_34 = "34.!"
        FIREFOX_35 = "35.!"
        FIREFOX_36 = "36.!"
        FIREFOX_37 = "37.!"
        FIREFOX_38 = "38.!"
        FIREFOX_39 = "39.!"
        FIREFOX_40 = "40.!"
        FIREFOX_41 = "41.!"
        FIREFOX_42 = "42.!"
        FIREFOX_43 = "43.!"
        FIREFOX_44 = "44.!"
        FIREFOX_45 = "45.!"
        FIREFOX_46 = "46.!"
        FIREFOX_47 = "47.!"
        FIREFOX_48 = "48.!"
        FIREFOX_49 = "49.!"
        FIREFOX_50 = "50.!"
        FIREFOX_51 = "51.!"
        FIREFOX_52 = "52.!"
        FIREFOX_53 = "53.!"
        FIREFOX_54 = "54.!"
        FIREFOX_55 = "55.!"
        FIREFOX_56 = "56.!"
        FIREFOX_57 = "57.!"
        FIREFOX_58 = "58.!"
        FIREFOX_59 = "59.!"
        FIREFOX_60 = "60.!"
        FIREFOX_61 = "61.!"
        FIREFOX_62 = "62.!"
        FIREFOX_63 = "63.!"
        FIREFOX_64 = "64.!"
        FIREFOX_65 = "65.!"
        FIREFOX_66 = "66.!"
        FIREFOX_67 = "67.!"
        FIREFOX_68 = "68.!"
        FIREFOX_69 = "69.!"
        FIREFOX_70 = "70.!"
        FIREFOX_71 = "71.!"
        FIREFOX_72 = "72.!"
        FIREFOX_73 = "73.!"
        FIREFOX_74 = "74.!"
        FIREFOX_75 = "75.!"
        FIREFOX_76 = "76.!"
        FIREFOX_77 = "77.!"
        FIREFOX_78 = "78.!"
        FIREFOX_79 = "79.!"
        FIREFOX_80 = "80.!"
        FIREFOX_81 = "81.!"
        FIREFOX_82 = "82.!"
        FIREFOX_83 = "83.!"
        FIREFOX_84 = "84.!"
        FIREFOX_85 = "85.!"
        FIREFOX_86 = "86.!"
        FIREFOX_87 = "87.!"
        FIREFOX_88 = "88.!"
        FIREFOX_89 = "89.!"
        FIREFOX_90 = "90.!"
        FIREFOX_91 = "91.!"
        FIREFOX_92 = "92.!"
        FIREFOX_93 = "93.!"
        FIREFOX_94 = "94.!"
        FIREFOX_95 = "95.!"
        FIREFOX_96 = "96.!"
        FIREFOX_97 = "97.!"
        FIREFOX_98 = "98.!"
        FIREFOX_99 = "99.!"
        FIREFOX_100 = "100.!"

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"
        ENROLLMENT_END = "enrollment end"

    EMAIL_EXPERIMENT_END_SUBJECT = "Action required: Please turn off your Experiment"
    EMAIL_ENROLLMENT_END_SUBJECT = "Action required: Please end experiment enrollment"

    TARGETING_VERSION = "version|versionCompare('{version}') >= 0"
    TARGETING_CHANNEL = 'browserSettings.update.channel == "{channel}"'

    TARGETING_CONFIGS = {
        TARGETING_NO_TARGETING.slug: TARGETING_NO_TARGETING,
        TARGETING_ALL_ENGLISH.slug: TARGETING_ALL_ENGLISH,
        TARGETING_US_ONLY.slug: TARGETING_US_ONLY,
        TARGETING_FIRST_RUN.slug: TARGETING_FIRST_RUN,
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug: (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION
        ),
        TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.slug: (
            TARGETING_FIRST_RUN_WINDOWS_1903_NEWER
        ),
        TARGETING_HOMEPAGE_GOOGLE.slug: TARGETING_HOMEPAGE_GOOGLE,
        TARGETING_URLBAR_FIREFOX_SUGGEST.slug: TARGETING_URLBAR_FIREFOX_SUGGEST,
    }

    class TargetingConfig(models.TextChoices):
        NO_TARGETING = TARGETING_NO_TARGETING.slug, TARGETING_NO_TARGETING.name
        ALL_ENGLISH = TARGETING_ALL_ENGLISH.slug, TARGETING_ALL_ENGLISH.name
        US_ONLY = TARGETING_US_ONLY.slug, TARGETING_US_ONLY.name
        TARGETING_FIRST_RUN = TARGETING_FIRST_RUN.slug, TARGETING_FIRST_RUN.name
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug
        ), TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.name
        TARGETING_FIRST_RUN_WINDOWS_1903_NEWER = (
            TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.slug
        ), TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.name
        TARGETING_HOMEPAGE_GOOGLE = (
            TARGETING_HOMEPAGE_GOOGLE.slug,
            TARGETING_HOMEPAGE_GOOGLE.name,
        )
        TARGETING_URLBAR_FIREFOX_SUGGEST = (
            TARGETING_URLBAR_FIREFOX_SUGGEST.slug,
            TARGETING_URLBAR_FIREFOX_SUGGEST.name,
        )

    # Telemetry systems including Firefox Desktop Telemetry v4 and Glean
    # have limits on the length of their unique identifiers, we should
    # limit the size of our slugs to the smallest limit, which is 80
    # for Firefox Desktop Telemetry v4.
    MAX_SLUG_LEN = 80

    MAX_DURATION = 1000

    # Bucket stuff
    BUCKET_TOTAL = 10000

    HYPOTHESIS_DEFAULT = """If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.
We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>
    """  # noqa

    MAX_PRIMARY_OUTCOMES = 2
    DEFAULT_PROPOSED_DURATION = 28
    DEFAULT_PROPOSED_ENROLLMENT = 7

    # Serializer validation errors
    ERROR_DUPLICATE_BRANCH_NAME = "Branch names must be unique."
    ERROR_REQUIRED_QUESTION = "This question may not be blank."
    ERROR_REQUIRED_FIELD = "This field may not be blank."
    ERROR_REQUIRED_FEATURE_CONFIG = (
        "You must select a feature configuration from the drop down."
    )
    ERROR_POPULATION_PERCENT_MIN = "Ensure this value is greater than or equal to 0.0001."

    # Analysis can be computed starting the week after enrollment
    # completion for "week 1" of the experiment. However, an extra
    # buffer day is added for Jetstream to compute the results.
    DAYS_UNTIL_ANALYSIS = 8

    # As a buffer, continue to pull in analysis from Jetstream
    # for 3 days after an experiment is complete.
    DAYS_ANALYSIS_BUFFER = 3

    KINTO_COLLECTION_APPLICATIONS = {
        settings.KINTO_COLLECTION_NIMBUS_DESKTOP: [
            APPLICATION_CONFIG_DESKTOP.slug,
        ],
        settings.KINTO_COLLECTION_NIMBUS_MOBILE: [
            APPLICATION_CONFIG_FENIX.slug,
            APPLICATION_CONFIG_IOS.slug,
        ],
    }

    KINTO_APPLICATION_COLLECTION = {
        application: collection
        for (collection, applications) in KINTO_COLLECTION_APPLICATIONS.items()
        for application in applications
    }

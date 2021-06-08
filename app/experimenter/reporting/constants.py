from django.db import models


class ReportLogConstants(object):
    class ExperimentStatus(models.TextChoices):
        DRAFT = "Draft"
        PREVIEW = "Preview"
        REVIEW = "Review"
        SHIP = "Ship"
        ACCEPTED = "Accepted"
        LIVE = "Live"
        COMPLETE = "Complete"

    class ExperimentType(models.TextChoices):
        NORMANDY_PREF = "Normandy-Pref"
        NORMANDY_ADDON = "Normandy-Addon"
        NORMANDY_ROLLOUT = "Normandy-Rollout"
        NIMBUS_DESKTOP = "Nimbus-Firefox-Desktop"
        NIMBUS_FENIX = "Nimbus-Fenix"
        NIMBUS_IOS = "Nimbus-Ios"

    class Event(models.TextChoices):
        CREATE = "Create"
        UPDATE = "Update"
        END = "End"

    class EventReason(models.TextChoices):
        NEW = "New"
        CLONE = "Clone"
        RELAUNCH = "Relaunch"
        STATUS_CHANGE = "Status Change"
        PAUSE = "Pause"
        RECIPE_CHANGE = "Recipe Change"
        QA_LAUNCH = "QA Launch"
        LAUNCH = "Launch"
        EXPERIMENT_COMPLETE = "Experiment Complete"
        FILTERING_ISSUE = "Filtering Issue"
        ENROLLMENT_ISSUE = "Enrollment Issue"
        EXPERIMENT_DESIGN_ISSUE = "Experiment Design Issue"
        RESULTS_ADDED = "Results Added"

    EVENT_PAIRS = {
        "Create": ["New", "Clone", "Relaunch"],
        "Update": [
            "Status Change",
            "Pause",
            "Recipe Change",
            "Qa Launch",
            "Launch",
            "Results Added",
        ],
        "End": [
            "Experiment Complete",
            "Filtering Issue",
            "Enrollment Issue",
            "Experiment Design Issue",
        ],
    }

    REPORT_HEADINGS = [
        "name",
        "url",
        "type",
        "projects",
        "time_in_draft",
        "time_in_preview",
        "time_in_review",
        "time_in_ship",
        "time_in_accepted",
        "time_in_live",
    ]

    EXCLUDED_PROJECTS = ["experiment tools"]

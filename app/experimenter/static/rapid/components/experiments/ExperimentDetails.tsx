import React from "react";
import { Link } from "react-router-dom";

import useInterval from "experimenter-rapid/components/experiments/useInterval";
import {
  featureOptions,
  audienceOptions,
  firefoxVersionOptions,
  firefoxChannelOptions,
} from "experimenter-rapid/components/forms/ExperimentFormOptions";
import {
  requestReview,
  fetchExperiment,
} from "experimenter-rapid/contexts/experiment/actions";
import {
  useExperimentState,
  useExperimentDispatch,
} from "experimenter-rapid/contexts/experiment/hooks";
import { ExperimentStatus } from "experimenter-rapid/types/experiment";

export const POLL_TIMEOUT = 30000;

const LabelledRow: React.FC<{ label: string; value?: string }> = ({
  children,
  label,
  value,
}) => {
  return (
    <tr>
      <th style={{ whiteSpace: "nowrap", width: "1%" }}>{label}</th>
      <td>
        {value}
        {children}
      </td>
    </tr>
  );
};

const displaySelectOptionLabels = (options, values) => {
  let selectedValue = values;
  if (!Array.isArray(values)) {
    selectedValue = [values];
  }

  const selectedOption = options.reduce((filtered, element) => {
    if (selectedValue.includes(element.value)) {
      filtered.push(element.label);
    }

    return filtered;
  }, []);
  return selectedOption.join(", ");
};

const ExperimentDetails: React.FC = () => {
  const experimentData = useExperimentState();
  const dispatch = useExperimentDispatch();

  const handleClickRequestApproval = async () => dispatch(requestReview());

  useInterval(() => {
    if (experimentData.slug) {
      dispatch(fetchExperiment(experimentData.slug));
    }
  }, POLL_TIMEOUT);

  let bugzilla_url;
  if (experimentData.bugzilla_url) {
    bugzilla_url = (
      <div>
        <small>
          Bugzilla ticket can be found{" "}
          <a
            href={experimentData.bugzilla_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            here
          </a>
        </small>
      </div>
    );
  }

  let monitoring_url;
  if (experimentData.monitoring_dashboard_url) {
    monitoring_url = (
      <>
        <h4 className="my-4">Monitoring</h4>
        <p>
          The live monitoring dashboard can be found here:
          <a
            href={experimentData.monitoring_dashboard_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            {" "}
            (link here)
          </a>
        </p>
      </>
    );
  }

  let analysis_report;
  if (
    [ExperimentStatus.LIVE, ExperimentStatus.COMPLETE].includes(
      experimentData.status,
    ) &&
    experimentData.recipe_slug
  ) {
    const slug_underscored = experimentData.recipe_slug.split("-").join("_");
    analysis_report = (
      <>
        <h4 className="my-4">Results</h4>
        <p>
          The results will be available 7 days after the experiment is launched.
          An email will be sent to you once we start recording data.
        </p>
        <p>
          The results can be found{" "}
          <a
            href={`https://protosaur.dev/partybal/${slug_underscored}.html`}
            rel="noopener noreferrer"
            target="_blank"
          >
            here
          </a>
        </p>
      </>
    );
  }

  const backButtonDisabled = ![
    ExperimentStatus.DRAFT,
    ExperimentStatus.REJECTED,
  ].includes(experimentData.status);

  let backButton = (
    <Link to={`/${experimentData.slug}/edit/`}>
      <button className="btn btn-primary">Back</button>
    </Link>
  );
  if (backButtonDisabled) {
    backButton = (
      <button disabled className="btn btn-secondary">
        Back
      </button>
    );
  }

  const requestButtonDisabled =
    experimentData.status !== ExperimentStatus.DRAFT;

  const buttonsShown = ![
    ExperimentStatus.LIVE,
    ExperimentStatus.COMPLETE,
  ].includes(experimentData.status);

  let changeStatusButtons;
  if (buttonsShown) {
    changeStatusButtons = (
      <div className="d-flex mt-4">
        <span>{backButton}</span>

        <span className="flex-grow-1 text-right">
          <button
            className={
              requestButtonDisabled ? "btn btn-secondary" : "btn btn-primary"
            }
            disabled={requestButtonDisabled}
            type="button"
            onClick={handleClickRequestApproval}
          >
            Request Approval
          </button>
        </span>
      </div>
    );
  }

  let rejectFeedback;

  if (experimentData.reject_feedback) {
    const messageDate = new Date(experimentData.reject_feedback.changed_on);
    rejectFeedback = (
      <>
        <h3 className="my-4">Review Feedback</h3>
        <div className="alert alert-secondary" role="alert">
          <p className="font-weight-bold"> {messageDate.toDateString()}</p>
          <p>Reject reason: {experimentData.reject_feedback.message}</p>
        </div>
      </>
    );
  }

  return (
    <div className="col pt-3">
      <div className="mb-4">
        <div className="mb-4">
          <h3 className="mb-0">
            {experimentData.name}{" "}
            <span className="badge badge-pill badge-small badge-secondary">
              {experimentData.status}
            </span>
          </h3>
          {experimentData.recipe_slug && (
            <p>
              <code>{experimentData.recipe_slug}</code>
            </p>
          )}
        </div>

        <table className="table table-bordered">
          <tbody>
            <LabelledRow
              label="Experiment Owner"
              value={experimentData.owner}
            />
            <LabelledRow label="Public Name" value={experimentData.name}>
              {bugzilla_url}
            </LabelledRow>
            <LabelledRow label="Hypothesis" value={experimentData.objectives} />
            <LabelledRow
              label="Feature"
              value={displaySelectOptionLabels(
                featureOptions,
                experimentData.features,
              )}
            />
            <LabelledRow
              label="Audience"
              value={displaySelectOptionLabels(
                audienceOptions,
                experimentData.audience,
              )}
            />
            <LabelledRow
              label="Firefox Minimum Version"
              value={displaySelectOptionLabels(
                firefoxVersionOptions,
                experimentData.firefox_min_version,
              )}
            />

            <LabelledRow
              label="Firefox Channel"
              value={displaySelectOptionLabels(
                firefoxChannelOptions,
                experimentData.firefox_channel,
              )}
            />
          </tbody>
        </table>

        {monitoring_url}

        {analysis_report}

        {rejectFeedback}
        {changeStatusButtons}
      </div>
    </div>
  );
};

export default ExperimentDetails;

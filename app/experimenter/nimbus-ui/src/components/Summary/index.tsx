/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import SummaryTimeline from "./SummaryTimeline";
import TableSummary from "./TableSummary";
import TableAudience from "./TableAudience";
import TableBranches from "./TableBranches";
import LinkExternal from "../LinkExternal";
import { getStatus } from "../../lib/experiment";
import LinkMonitoring from "../LinkMonitoring";
import { getConfigLabel, ConfigOptions } from "../../lib/getConfigLabel";
import NotSet from "../NotSet";
import { ReactComponent as ExternalIcon } from "../../images/external.svg";

type SummaryProps = {
  experiment: getExperiment_experimentBySlug;
};

const Summary = ({ experiment }: SummaryProps) => {
  const status = getStatus(experiment);
  const branchCount = [
    experiment.referenceBranch,
    ...(experiment.treatmentBranches || []),
  ].filter((branch) => !!branch).length;

  return (
    <div data-testid="summary">
      <LinkMonitoring {...experiment} />
      <h2 className="h5 mb-3">Timeline</h2>
      <SummaryTimeline {...{ experiment }} />

      <div className="d-flex flex-row justify-content-between">
        <h2 className="h5 mb-3">Summary</h2>
        {!status.draft && !status.review && (
          <span>
            <LinkExternal
              href={`/api/v6/experiments/${experiment.slug}/`}
              data-testid="link-json"
            >
              <span className="mr-1 align-middle">
                See full JSON representation
              </span>
              <ExternalIcon />
            </LinkExternal>
          </span>
        )}
      </div>
      <TableSummary {...{ experiment }} />

      <h2 className="h5 mb-3">Audience</h2>
      <TableAudience {...{ experiment }} />

      <h2 className="h5 mb-3" data-testid="branches-section-title">
        Branches ({branchCount})
      </h2>
      <TableBranches {...{ experiment }} />
    </div>
  );
};

export const displayConfigLabelOrNotSet = (
  value: string | null,
  options: ConfigOptions,
) => {
  if (!value) return <NotSet />;
  return getConfigLabel(value, options);
};

export default Summary;

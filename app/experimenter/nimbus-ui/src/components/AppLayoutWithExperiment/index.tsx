/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useState } from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import HeaderExperiment from "../HeaderExperiment";
import PageLoading from "../PageLoading";
import PageExperimentNotFound from "../PageExperimentNotFound";
import { useAnalysis, useExperiment } from "../../hooks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import AppLayout from "../AppLayout";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { AnalysisData } from "../../lib/visualization/types";

type AppLayoutWithExperimentChildrenProps = {
  experiment: getExperiment_experimentBySlug;
  review: {
    isMissingField: (fieldName: string) => boolean;
    refetch: () => void;
  };
  analysis?: AnalysisData;
};

type AppLayoutWithExperimentProps = {
  children: (
    props: AppLayoutWithExperimentChildrenProps,
  ) => React.ReactNode | null;
  testId: string;
  title?: string;
  polling?: boolean;
  sidebar?: boolean;
} & RouteComponentProps;

export const POLL_INTERVAL = 30000;

const experimentActive = (status: NimbusExperimentStatus | null): boolean => {
  if (!status) return false;

  return [
    NimbusExperimentStatus.LIVE,
    NimbusExperimentStatus.COMPLETE,
  ].includes(status);
};

const AppLayoutWithExperiment = ({
  children,
  testId,
  title,
  sidebar = true,
  polling = false,
}: AppLayoutWithExperimentProps) => {
  const { slug } = useParams();
  const {
    experiment,
    notFound,
    loading: experimentLoading,
    startPolling,
    stopPolling,
    review,
  } = useExperiment(slug);
  // We won't know if an analysis lookup is required until the initial experiment query
  // is complete and we inspect its status. To prevent content from flashing on the screen
  // between the experiment and analysis requests, assume we need to wait for analysis
  // until we can prove otherwise.
  const [analysisRequired, setAnalysisRequired] = useState<boolean>(true);
  const [analysisFetched, setAnalysisFetched] = useState<boolean>(false);

  const {
    execute: fetchAnalysis,
    result: analysis,
    loading: analysisLoading,
  } = useAnalysis();

  useEffect(() => {
    if (
      !analysisFetched &&
      !experimentLoading &&
      experimentActive(experiment?.status)
    ) {
      fetchAnalysis([experiment?.slug]);
      setAnalysisFetched(true);
    }
  }, [fetchAnalysis, experimentLoading, experiment, analysisFetched]);

  useEffect(() => {
    if (!experimentLoading && !analysisLoading) {
      setAnalysisRequired(false);
    }
  }, [experimentLoading, analysisLoading]);

  useEffect(() => {
    if (polling && experiment) {
      startPolling(POLL_INTERVAL);
    }
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling, experiment, polling]);

  if (experimentLoading || analysisRequired) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const { name, status } = experiment;

  return (
    <Layout
      {...{ sidebar, children, review, analysis }}
      status={experiment.status}
    >
      <section data-testid={testId}>
        <HeaderExperiment
          {...{
            slug,
            name,
            status,
          }}
        />
        {title && (
          <h2 className="mt-3 mb-4 h4" data-testid="page-title">
            {title}
          </h2>
        )}
        <div className="mt-4">{children({ experiment, review, analysis })}</div>
      </section>
    </Layout>
  );
};

type LayoutProps = {
  sidebar: boolean;
  children: React.ReactElement;
  status: NimbusExperimentStatus | null;
  review: {
    ready: boolean;
    invalidPages: string[];
  };
  analysis?: AnalysisData;
};

const Layout = ({ sidebar, children, review, status, analysis }: LayoutProps) =>
  sidebar ? (
    <AppLayoutWithSidebar {...{ status, review, analysis }}>
      {children}
    </AppLayoutWithSidebar>
  ) : (
    <AppLayout>{children}</AppLayout>
  );

export default AppLayoutWithExperiment;

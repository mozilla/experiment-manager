import { RouteComponentProps, useParams } from "@reach/router";
import classnames from "classnames";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import Scrollspy from "react-scrollspy";
import { useConfig } from "../../hooks";
import { ReactComponent as Airplane } from "../../images/airplane.svg";
import { ReactComponent as ChevronLeft } from "../../images/chevron-left.svg";
import { StatusCheck } from "../../lib/experiment";
import { AnalysisData, MetadataPoint } from "../../lib/visualization/types";
import { analysisAvailable } from "../../lib/visualization/utils";
import { getConfig_nimbusConfig_outcomes } from "../../types/getConfig";
import { DisabledItem } from "../DisabledItem";
import LinkExternal from "../LinkExternal";
import { LinkNav } from "../LinkNav";
import { ReactComponent as BarChart } from "./bar-chart.svg";

export const RESULTS_LOADING_TEXT = "Checking results availability...";
const baseLinkClass = "d-block inherit-color mb-2";

const getSidebarItems = (
  metrics: { [metric: string]: string },
  title: string,
) => {
  const sidebarItems = Object.keys(metrics).map((sidebarKey) => (
    <a
      href={`#${sidebarKey}`}
      key={sidebarKey}
      className={classnames(baseLinkClass, "font-weight-normal ml-3")}
    >
      {metrics[sidebarKey]}
    </a>
  ));
  sidebarItems.unshift(
    <p key={title} className="mb-2">
      {title}
    </p>,
  );
  return sidebarItems;
};

const outcomeToMapping = (
  outcomeSlugs: (string | null)[],
  configOutcomes: (getConfig_nimbusConfig_outcomes | null)[] | null,
) => {
  return outcomeSlugs.reduce((acc: { [key: string]: string }, slug) => {
    const configOutcome = configOutcomes?.find((set) => {
      return set?.slug === slug;
    });

    if (configOutcome) {
      acc[slug as string] = configOutcome.friendlyName!;
    }

    return acc;
  }, {});
};

const otherMetricsToFriendlyName = (
  otherMetrics: { [metric: string]: string },
  metricsMetaData: { [metric: string]: MetadataPoint },
) => {
  const newMap: { [key: string]: string } = {};
  Object.keys(otherMetrics).map(
    (metric) =>
      (newMap[metric] =
        metricsMetaData[metric]?.friendly_name || otherMetrics[metric]),
  );
  return newMap;
};

type AppLayoutSidebarLockedProps = {
  testid?: string;
  children: React.ReactNode;
  status: StatusCheck;
  analysis?: AnalysisData;
  analysisLoadingInSidebar?: boolean;
  analysisError?: Error;
  primaryOutcomes: (string | null)[] | null;
  secondaryOutcomes: (string | null)[] | null;
} & RouteComponentProps;

export const AppLayoutSidebarLocked = ({
  children,
  testid = "AppLayoutSidebarLocked",
  status,
  analysis,
  analysisLoadingInSidebar = false,
  analysisError,
  primaryOutcomes,
  secondaryOutcomes,
}: AppLayoutSidebarLockedProps) => {
  const { slug } = useParams();
  const { outcomes } = useConfig();
  const primaryMetrics = outcomeToMapping(primaryOutcomes || [], outcomes);
  const secondaryMetrics = outcomeToMapping(secondaryOutcomes || [], outcomes);
  const otherMetrics = otherMetricsToFriendlyName(
    analysis?.other_metrics || {},
    analysis?.metadata?.metrics || {},
  );

  const sidebarKeys = [
    "monitoring",
    "overview",
    "results-summary",
    "primary-metrics",
  ]
    .concat(Object.keys(primaryMetrics || []))
    .concat("secondary-metrics")
    .concat(Object.keys(secondaryMetrics || []))
    .concat("default-metrics")
    .concat(Object.keys(otherMetrics || []));

  return (
    <Container fluid className="h-100vh" data-testid={testid}>
      <Row className="h-md-100">
        <Col
          md="3"
          lg="3"
          xl="2"
          className="bg-light pt-2 border-right shadow-sm"
        >
          <nav
            data-testid="nav-sidebar"
            className="navbar fixed-top col-xl-2 col-lg-3 col-md-3 px-4 py-3"
          >
            <Nav
              className="flex-column font-weight-semibold mx-2 w-100"
              as="ul"
            >
              <LinkNav
                storiesOf="pages/Home"
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Experiments
              </LinkNav>
              <LinkNav
                route={slug}
                storiesOf={"pages/Summary"}
                testid={"nav-summary"}
              >
                <Airplane className="sidebar-icon" />
                Summary
              </LinkNav>
              {analysisAvailable(analysis) ? (
                <>
                  <LinkNav
                    route={`${slug}/results`}
                    storiesOf={"pages/Results"}
                    testid={"nav-results"}
                  >
                    <BarChart className="sidebar-icon" />
                    Results
                  </LinkNav>
                  <Scrollspy
                    items={sidebarKeys}
                    className="text-dark mt-2"
                    currentClassName="text-primary"
                  >
                    <a href="#monitoring" className={baseLinkClass}>
                      Monitoring
                    </a>
                    <a href="#overview" className={baseLinkClass}>
                      Overview
                    </a>
                    <a href="#results-summary" className={baseLinkClass}>
                      Results Summary
                    </a>
                    {Object.keys(primaryMetrics).length &&
                      getSidebarItems(primaryMetrics, "Primary Metrics")}
                    {Object.keys(secondaryMetrics).length &&
                      getSidebarItems(secondaryMetrics, "Secondary Metrics")}
                    {otherMetrics &&
                      getSidebarItems(otherMetrics, "Default Metrics")}
                  </Scrollspy>
                </>
              ) : (
                <DisabledItem name="Results" testId="show-no-results">
                  {status?.accepted ? (
                    "Waiting for experiment to launch"
                  ) : analysisLoadingInSidebar ? (
                    RESULTS_LOADING_TEXT
                  ) : analysisError ? (
                    <>
                      Could not get visualization data. Please contact data
                      science in{" "}
                      <LinkExternal href="https://mozilla.slack.com/archives/C0149JH7C1M">
                        #cirrus
                      </LinkExternal>
                      .
                    </>
                  ) : (
                    "Experiment results not yet ready"
                  )}
                </DisabledItem>
              )}
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10 pt-5 px-md-3 px-lg-5">
          <main className="container-lg mx-auto">{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

export default AppLayoutSidebarLocked;

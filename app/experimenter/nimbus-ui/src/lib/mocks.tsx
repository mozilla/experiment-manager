/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  InMemoryCache,
  ApolloClient,
  ApolloProvider,
  ApolloLink,
  Operation,
  FetchResult,
} from "@apollo/client";
import { Observable } from "@apollo/client/utilities";
import { MockLink, MockedResponse } from "@apollo/client/testing";
import { equal } from "@wry/equality";
import { DocumentNode, print } from "graphql";
import { cacheConfig } from "../services/apollo";
import {
  GET_EXPERIMENTS_QUERY,
  GET_EXPERIMENT_QUERY,
} from "../gql/experiments";
import {
  getExperiment,
  getExperiment_experimentBySlug,
} from "../types/getExperiment";
import { getConfig_nimbusConfig } from "../types/getConfig";
import {
  getAllExperiments,
  getAllExperiments_experiments,
} from "../types/getAllExperiments";
import { GET_CONFIG_QUERY } from "../gql/config";
import { NimbusExperimentStatus } from "../types/globalTypes";
import { getStatus } from "./experiment";
import {
  NimbusFeatureConfigApplication,
  NimbusProbeKind,
  ExperimentInput,
} from "../types/globalTypes";
import { ExperimentReview } from "../hooks";

export interface MockedProps {
  config?: Partial<typeof MOCK_CONFIG> | null;
  childProps?: object;
  children?: React.ReactElement;
  mocks?: MockedResponse<Record<string, any>>[];
  addTypename?: boolean;
  link?: ApolloLink;
}

export interface MockedState {
  client: ApolloClient<any>;
}

export const MOCK_CONFIG: getConfig_nimbusConfig = {
  __typename: "NimbusConfigurationType",
  application: [
    {
      __typename: "NimbusLabelValueType",
      label: "Desktop",
      value: "DESKTOP",
    },
  ],
  channel: [
    {
      __typename: "NimbusLabelValueType",
      label: "Desktop Beta",
      value: "DESKTOP_BETA",
    },
    {
      __typename: "NimbusLabelValueType",
      label: "Desktop Nightly",
      value: "DESKTOP_NIGHTLY",
    },
    {
      __typename: "NimbusLabelValueType",
      label: "Platypus Doorstop",
      value: "PLATYPUS_DOORSTOP",
    },
  ],
  applicationChannels: [
    {
      __typename: "ApplicationChannel",
      label: "Desktop",
      channels: [
        "Desktop Unbranded",
        "Desktop Nightly",
        "Desktop Beta",
        "Desktop Release",
      ],
    },
    {
      __typename: "ApplicationChannel",
      label: "Fenix",
      channels: ["Fenix Nightly", "Fenix Beta", "Fenix Release"],
    },
  ],
  featureConfig: [
    {
      __typename: "NimbusFeatureConfigType",
      id: "1",
      name: "Picture-in-Picture",
      slug: "picture-in-picture",
      description:
        "Quickly above also mission action. Become thing item institution plan.\nImpact friend wonder. Interview strategy nature question. Admit room without impact its enter forward.",
      application: NimbusFeatureConfigApplication.FENIX,
      ownerEmail: "sheila43@yahoo.com",
      schema: null,
    },
    {
      __typename: "NimbusFeatureConfigType",
      id: "2",
      name: "Mauris odio erat",
      slug: "mauris-odio-erat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusFeatureConfigApplication.FENIX,
      ownerEmail: "dude23@yahoo.com",
      schema: '{ "sample": "schema" }',
    },
  ],
  firefoxMinVersion: [
    {
      __typename: "NimbusLabelValueType",
      label: "Firefox 80",
      value: "FIREFOX_80",
    },
  ],
  probeSets: [
    {
      __typename: "NimbusProbeSetType",
      id: "1",
      name: "Probe Set A",
      slug: "probe-set-a",
      probes: [
        {
          __typename: "NimbusProbeType",
          id: "1",
          kind: NimbusProbeKind.EVENT,
          name: "Public-key intangible Graphical User Interface",
          eventCategory: "persevering-intangible-productivity",
          eventMethod: "monitored-system-worthy-core",
          eventObject: "ameliorated-uniform-protocol",
          eventValue: "front-line-5thgeneration-product",
        },
        {
          __typename: "NimbusProbeType",
          id: "2",
          kind: NimbusProbeKind.SCALAR,
          name: "Total didactic moderator",
          eventCategory: "horizontal-bifurcated-attitude",
          eventMethod: "optimized-homogeneous-system-engine",
          eventObject: "virtual-discrete-customer-loyalty",
          eventValue: "automated-national-infrastructure",
        },
      ],
    },
    {
      __typename: "NimbusProbeSetType",
      id: "2",
      name: "Probe Set B",
      slug: "probe-set-b",
      probes: [],
    },
    {
      __typename: "NimbusProbeSetType",
      id: "3",
      name: "Probe Set C",
      slug: "probe-set-c",
      probes: [],
    },
  ],
  targetingConfigSlug: [
    {
      __typename: "NimbusLabelValueType",
      label: "Us Only",
      value: "US_ONLY",
    },
  ],
  hypothesisDefault: "Enter a hypothesis",
};

// Disabling this rule for now because we'll eventually
// be using props from MockedProps.
// eslint-disable-next-line no-empty-pattern
export function createCache({ config = {} }: MockedProps = {}) {
  const cache = new InMemoryCache(cacheConfig);

  cache.writeQuery({
    query: GET_CONFIG_QUERY,
    data: {
      nimbusConfig: { ...MOCK_CONFIG, ...config },
    },
  });

  return cache;
}

export class MockedCache extends React.Component<MockedProps, MockedState> {
  constructor(props: MockedProps) {
    super(props);
    this.state = {
      client: new ApolloClient({
        cache: createCache(props),
        link:
          props.link ||
          new MockLink(props.mocks || [], props.addTypename || true),
      }),
    };
  }

  render() {
    const { children, childProps } = this.props;
    return children ? (
      <ApolloProvider client={this.state.client}>
        {React.cloneElement(React.Children.only(children), { ...childProps })}
      </ApolloProvider>
    ) : null;
  }

  componentWillUnmount() {
    this.state.client.stop();
  }
}

type ResultFunction = (operation: Operation) => FetchResult;

type SimulatedMockedResponses = ReadonlyArray<{
  request: MockedResponse["request"];
  result: ResultFunction;
  delay?: number;
}>;

export class SimulatedMockLink extends ApolloLink {
  constructor(
    public mockedResponses: SimulatedMockedResponses,
    public addTypename: boolean = true,
  ) {
    super();
  }

  public request(operation: Operation): Observable<FetchResult> | null {
    const response = this.mockedResponses.find((response) =>
      equal(operation.query, response.request.query),
    );

    if (!response) {
      this.onError(
        new Error(
          `No more mocked responses for the query: ${print(
            operation.query,
          )}, variables: ${JSON.stringify(operation.variables)}`,
        ),
      );
      return null;
    }

    const { result, delay } = response!;

    return new Observable((observer) => {
      const timer = setTimeout(
        () => {
          observer.next(
            typeof result === "function"
              ? (result(operation) as FetchResult)
              : result,
          );
          observer.complete();
        },
        delay ? delay : 0,
      );

      return () => clearTimeout(timer);
    });
  }
}

export function mockExperimentQuery<
  T extends getExperiment["experimentBySlug"] = getExperiment_experimentBySlug
>(
  slug: string,
  modifications: Partial<getExperiment["experimentBySlug"]> = {},
): {
  mock: MockedResponse<Record<string, any>>;
  experiment: T;
} {
  let experiment: getExperiment["experimentBySlug"] = Object.assign(
    {
      __typename: "NimbusExperimentType",
      id: 1,
      owner: {
        __typename: "NimbusExperimentOwner",
        email: "example@mozilla.com",
      },
      name: "Open-architected background installation",
      slug,
      status: "DRAFT",
      monitoringDashboardUrl: "https://grafana.telemetry.mozilla.org",
      hypothesis: "Realize material say pretty.",
      application: "DESKTOP",
      publicDescription:
        "Official approach present industry strategy dream piece.",
      referenceBranch: {
        __typename: "NimbusBranchType",
        name: "User-centric mobile solution",
        slug: "user-centric-mobile-solution",
        description: "Behind almost radio result personal none future current.",
        ratio: 1,
        featureValue: '{"environmental-fact": "really-citizen"}',
        featureEnabled: true,
      },
      featureConfig: null,
      treatmentBranches: [
        {
          __typename: "NimbusBranchType",
          name: "Managed zero tolerance projection",
          slug: "managed-zero-tolerance-projection",
          description: "Next ask then he in degree order.",
          ratio: 1,
          featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
          featureEnabled: true,
        },
      ],
      primaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
      ],
      secondaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "2",
          slug: "feature_b",
          name: "Feature B",
        },
      ],
      channel: "DESKTOP_NIGHTLY",
      firefoxMinVersion: "FIREFOX_80",
      targetingConfigSlug: "US_ONLY",
      targetingConfigTargeting: "localeLanguageCode == 'en' && region == 'US'",
      populationPercent: "40",
      totalEnrolledClients: 68000,
      proposedEnrollment: 1,
      proposedDuration: 28,
      readyForReview: {
        ready: true,
        message: {},
        __typename: "NimbusReadyForReviewType",
      },
      startDate: new Date().toISOString(),
      endDate: new Date(Date.now() + 12096e5).toISOString(),
      riskMitigationLink: "https://docs.google.com/document/d/banzinga/edit",
      documentationLinks: [
        { title: "Bingo bongo", link: "https://bingo.bongo" },
      ],
    },
    modifications,
  );

  if (modifications === null) {
    experiment = null;
  }

  return {
    mock: {
      request: {
        query: GET_EXPERIMENT_QUERY,
        variables: {
          slug,
        },
      },
      result: {
        data: {
          experimentBySlug: experiment,
        },
      },
    },
    experiment: experiment as T,
  };
}

export const MOCK_REVIEW: ExperimentReview = {
  ready: true,
  invalidPages: [],
  missingFields: [],
  isMissingField: () => false,
  refetch: () => {},
};

export const mockExperimentMutation = (
  mutation: DocumentNode,
  input: ExperimentInput,
  key: string,
  {
    status = 200,
    message = "success",
    experiment,
  }: {
    status?: number;
    message?: string | Record<string, any>;
    experiment?: Record<string, any> | null;
  },
) => {
  return {
    request: {
      query: mutation,
      variables: {
        input,
      },
    },
    result: {
      errors: undefined as undefined | any[],
      data: {
        [key]: {
          clientMutationId: "8675309",
          message,
          status,
          nimbusExperiment: experiment,
        },
      },
    },
  };
};

export const mockGetStatus = (status: NimbusExperimentStatus | null) => {
  const { experiment } = mockExperimentQuery("boo", { status });
  return getStatus(experiment);
};

const fiveDaysAgo = new Date();
fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);

/** Creates a single mock experiment suitable for getAllExperiments queries.  */
export function mockSingleDirectoryExperiment(
  overrides: Partial<getAllExperiments_experiments> = {},
): getAllExperiments_experiments {
  return {
    __typename: "NimbusExperimentType",
    slug: `some-experiment-${Math.round(Math.random() * 100)}`,
    owner: {
      __typename: "NimbusExperimentOwner",
      username: "example@mozilla.com",
    },
    monitoringDashboardUrl:
      "https://grafana.telemetry.mozilla.org/d/XspgvdxZz/experiment-enrollment?orgId=1&var-experiment_id=bug-1668861-pref-measure-set-to-default-adoption-impact-of-chang-release-81-83",
    name: "Open-architected background installation",
    status: NimbusExperimentStatus.COMPLETE,
    featureConfig: {
      __typename: "NimbusFeatureConfigType",
      slug: "newtab",
      name: "New tab",
    },
    proposedEnrollment: 7,
    proposedDuration: 28,
    startDate: fiveDaysAgo.toISOString(),
    endDate: new Date(Date.now() + 12096e5).toISOString(),
    ...overrides,
  };
}

export function mockDirectoryExperiments(
  overrides: Partial<getAllExperiments_experiments>[] = [
    {
      status: NimbusExperimentStatus.DRAFT,
      startDate: null,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.REVIEW,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.REVIEW,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.COMPLETE,
    },
    {
      featureConfig: null,
    },
  ],
): getAllExperiments_experiments[] {
  return overrides.map(mockSingleDirectoryExperiment);
}

/** Creates a bunch of experiments for the Directory page  */
export function mockDirectoryExperimentsQuery(
  overrides?: Partial<getAllExperiments_experiments>[],
): MockedResponse<getAllExperiments> {
  const experiments = mockDirectoryExperiments(overrides);
  return {
    request: {
      query: GET_EXPERIMENTS_QUERY,
    },
    result: {
      data: experiments.length ? { experiments } : null,
    },
  };
}

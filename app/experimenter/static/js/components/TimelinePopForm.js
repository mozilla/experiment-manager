import PropTypes from "prop-types";
import React from "react";
import { Button, Container, Row, Col } from "react-bootstrap";
import { boundClass } from "autobind-decorator";
import { fromJS, Map } from "immutable";

import DesignInput from "experimenter/components/DesignInput";
import LabeledMultiSelect from "experimenter/components/LabeledMultiSelect";

import { makeApiRequest } from "experimenter/utils/api";
import {
  VERSION_CHOICES,
  PLAYBOOK_CHOICES,
  PROPOSED_START_DATE_HELP,
  PROPOSED_DURATION_HELP,
  PROPOSED_ENROLLMENT_HELP,
  CHANNEL_HELP,
  POPULATION_PERCENT_HELP,
  VERSION_HELP,
  PLATFORM_HELP,
  CLIENT_MATCHING_HELP,
  COUNTRIES_LOCALES_HELP,
  ROLLOUT_PLAYBOOK_HELP,
} from "experimenter/components/constants";

@boundClass
class TimelinePopForm extends React.PureComponent {
  static propTypes = {
    slug: PropTypes.string,
    shouldHavePopPercent: PropTypes.string,
    allCountries: PropTypes.array,
    allLocales: PropTypes.array,
    experimentType: PropTypes.string,
  };

  constructor(props) {
    super(props);

    this.state = {
      data: new Map(),
      errors: new Map(),
      loaded: false,
      saving: false,
    };
  }

  getEndpointUrl() {
    return `experiments/${this.props.slug}/timeline-population/`;
  }

  async componentDidMount() {
    try {
      const data = await makeApiRequest(this.getEndpointUrl());
      this.setState({
        loaded: true,
        data: fromJS(data),
      });
    } catch (error) {
      console.error(error.message);
    }
  }

  handleDataChange(key, value) {
    if (value === "") {
      value = null;
    }
    this.setState(({ data }) => ({
      data: data.set(key, value),
    }));
  }

  handleMultiSelectDataChange(selectedOptions, name) {
    if (selectedOptions == null) {
      selectedOptions = [];
    }
    this.setState(({ data }) => ({
      data: data.set(name, fromJS(selectedOptions)),
    }));
  }

  displayPopulationPercent() {
    if (this.props.shouldHavePopPercent) {
      return (
        <DesignInput
          label="Population Percentage"
          name="population_percent"
          id="id_population_percent"
          onChange={(value) => {
            this.handleDataChange("population_percent", value);
          }}
          value={this.state.data.get("population_percent")}
          error={this.state.errors.get("population_percent", "")}
          helpContent={POPULATION_PERCENT_HELP}
          labelColumnWidth={2}
        />
      );
    }
  }

  displayEnrollmentDuration() {
    if (this.props.experimentType != "rollout") {
      return (
        <DesignInput
          label="Proposed Enrollment Duration (days)"
          name="proposed_enrollment"
          id="id_proposed_enrollment"
          onChange={(value) => {
            this.handleDataChange("proposed_enrollment", value);
          }}
          value={this.state.data.get("proposed_enrollment")}
          error={this.state.errors.get("proposed_enrollment", "")}
          helpContent={PROPOSED_ENROLLMENT_HELP}
          labelColumnWidth={2}
          optional={true}
        />
      );
    }
  }

  displayRolloutPlaybook() {
    if (this.props.experimentType === "rollout") {
      return (
        <DesignInput
          as="select"
          label="Rollout Playbook"
          name="rollout_playbook"
          id="id_rollout_playbook"
          onChange={(value) => {
            this.handleDataChange("rollout_playbook", value);
          }}
          value={this.state.data.get("rollout_playbook")}
          error={this.state.errors.get("rollout_playbook", "")}
          labelColumnWidth={2}
          helpContent={ROLLOUT_PLAYBOOK_HELP}
          helpIsExternalLink={true}
        >
          {this.displayOptions(PLAYBOOK_CHOICES)}
        </DesignInput>
      );
    }
  }

  displayOptions(choices) {
    let choicesJSX = [];

    for (const choice of choices) {
      choicesJSX.push(<option value={choice[0]}>{choice[1]}</option>);
    }

    return choicesJSX;
  }

  async handleSubmit(event, redirectUrl) {
    event.preventDefault();

    this.setState({ saving: true });
    const requestSave = makeApiRequest(this.getEndpointUrl(), {
      method: "PUT",
      data: this.state.data.toJS(),
    });

    requestSave
      .then(() => {
        location.replace(redirectUrl);
      })
      .catch((err) => {
        this.setState({
          errors: fromJS(err.data),
        });

        const invalid = document.querySelector(".is-invalid");
        if (invalid) {
          invalid.scrollIntoView();
        }
      })
      .finally(() => {
        this.setState({
          saving: false,
        });
      });
  }

  handleSubmitSave(event) {
    this.handleSubmit(event, `/experiments/${this.props.slug}/`);
  }

  handleSubmitContinue(event) {
    this.handleSubmit(event, `/experiments/${this.props.slug}/edit-design/`);
  }

  render() {
    if (!this.state.loaded) {
      return (
        <Container>
          <div className="fa-5x" data-testId="spinner">
            <Row className="justify-content-center">
              <i className="fas fa-spinner fa-spin" />
            </Row>
          </div>
        </Container>
      );
    }
    return (
      <div className="page-edit-timeline-and-population">
        <Container>
          <form onSubmit={this.handleSubmit}>
            <Row className="mb-3 mt-3">
              <h4 className="col-10 offset-2">Delivery Timeline</h4>
            </Row>
            <DesignInput
              type="date"
              label="Proposed Start Date"
              name="proposed_start_date"
              id="id_proposed_start_date"
              onChange={(value) => {
                this.handleDataChange("proposed_start_date", value);
              }}
              value={this.state.data.get("proposed_start_date")}
              error={this.state.errors.get("proposed_start_date", "")}
              helpContent={PROPOSED_START_DATE_HELP}
              labelColumnWidth={2}
            />
            <DesignInput
              label="Proposed Total Duration (days)"
              name="proposed_duration"
              id="id_proposed_duration"
              onChange={(value) => {
                this.handleDataChange("proposed_duration", value);
              }}
              value={this.state.data.get("proposed_duration")}
              error={this.state.errors.get("proposed_duration", "")}
              helpContent={PROPOSED_DURATION_HELP}
              labelColumnWidth={2}
            />
            {this.displayEnrollmentDuration()}
            {this.displayRolloutPlaybook()}
            <hr className="heavy-line my-5" />
            <Row className="mb-3 mt-3">
              <h4 className="col-10 offset-2">Delivery Population</h4>
            </Row>
            {this.displayPopulationPercent()}
            <DesignInput
              as="select"
              label="Firefox Channel"
              name="firefox_channel"
              id="id_firefox_channel"
              onChange={(value) => {
                this.handleDataChange("firefox_channel", value);
              }}
              value={this.state.data.get("firefox_channel")}
              error={this.state.errors.get("firefox_channel", "")}
              helpContent={CHANNEL_HELP}
              labelColumnWidth={2}
              helpIsExternalLink={true}
            >
              <option>Firefox Channel</option>
              <option>Nightly</option>
              <option>Beta</option>
              <option>Release</option>
            </DesignInput>
            <Row>
              <Col md={6}>
                <DesignInput
                  as="select"
                  label="Firefox Min Version"
                  name="firefox_min_version"
                  id="id_firefox_min_version"
                  onChange={(value) => {
                    this.handleDataChange("firefox_min_version", value);
                  }}
                  value={this.state.data.get("firefox_min_version")}
                  error={this.state.errors.get("firefox_min_version", "")}
                  helpContent={VERSION_HELP}
                  labelColumnWidth={4}
                  helpIsExternalLink={true}
                >
                  {this.displayOptions(VERSION_CHOICES)}
                </DesignInput>
              </Col>
              <Col md={6}>
                <DesignInput
                  as="select"
                  label="Firefox Max Version"
                  name="firefox_max_version"
                  id="id_firefox_max_version"
                  onChange={(value) => {
                    this.handleDataChange("firefox_max_version", value);
                  }}
                  value={this.state.data.get("firefox_max_version")}
                  error={this.state.errors.get("firefox_max_version", "")}
                  labelColumnWidth={4}
                  noHelpLink={true}
                >
                  {this.displayOptions(VERSION_CHOICES)}
                </DesignInput>
              </Col>
            </Row>
            <LabeledMultiSelect
              options={this.props.allLocales}
              label="Locales"
              name="locales"
              id="id_locales"
              onChange={this.handleMultiSelectDataChange}
              value={
                this.state.data.get("locales")
                  ? this.state.data.get("locales", []).toJS()
                  : []
              }
              error={this.state.errors.get("locales", "")}
              helpContent={COUNTRIES_LOCALES_HELP}
              labelColumnWidth={2}
              optional={true}
              placeholder="All Locales"
            />
            <LabeledMultiSelect
              options={this.props.allCountries}
              label="Countries"
              name="countries"
              id="id_countries"
              onChange={this.handleMultiSelectDataChange}
              value={
                this.state.data.get("countries")
                  ? this.state.data.get("countries", []).toJS()
                  : []
              }
              error={this.state.errors.get("countries", "")}
              helpContent={COUNTRIES_LOCALES_HELP}
              labelColumnWidth={2}
              optional={true}
              placeholder="All Countries"
            />
            <DesignInput
              as="select"
              multi
              label="Platform"
              name="platform"
              id="id_platform"
              onChange={(value) => {
                this.handleDataChange("platform", value);
              }}
              value={this.state.data.get("platform")}
              error={this.state.errors.get("platform", "")}
              helpContent={PLATFORM_HELP}
              labelColumnWidth={2}
              optional={true}
            >
              <option>All Platforms</option>
              <option>All Windows</option>
              <option>All Mac</option>
              <option>All Linux</option>
            </DesignInput>
            <DesignInput
              label="Population filtering"
              name="client_matching"
              id="id_client_matching"
              onChange={(value) => {
                this.handleDataChange("client_matching", value);
              }}
              value={this.state.data.get("client_matching")}
              error={this.state.errors.get("client_matching", "")}
              helpContent={CLIENT_MATCHING_HELP}
              as="textarea"
              rows="10"
              labelColumnWidth={2}
              optional={true}
            />
            <Row>
              <Col className="text-right">
                <a
                  className="mr-1 btn btn-link"
                  href={`/experiments/${this.props.slug}/`}
                >
                  <span className="fas fa-times" /> Cancel Editing
                </a>

                <Button
                  disabled={this.state.saving}
                  variant="primary"
                  type="submit"
                  className="mr-1"
                  onClick={this.handleSubmitSave}
                >
                  <span className="fas fa-save" /> Save Draft
                </Button>

                <Button
                  disabled={this.state.saving}
                  id="save-and-continue-btn"
                  variant="primary"
                  type="submit"
                  onClick={this.handleSubmitContinue}
                >
                  <span className="fas fa-save" /> Save Draft and Continue
                </Button>
              </Col>
            </Row>
          </form>
        </Container>
      </div>
    );
  }
}

export default TimelinePopForm;

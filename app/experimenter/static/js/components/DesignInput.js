import { boundClass } from "autobind-decorator";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, FormControl, FormLabel } from "react-bootstrap";

import Error from "experimenter/components/Error";
import HelpBox from "experimenter/components/HelpBox";

@boundClass
class DesignInput extends React.PureComponent {
  static propTypes = {
    as: PropTypes.string,
    children: PropTypes.oneOfType([
      PropTypes.arrayOf(PropTypes.node),
      PropTypes.node,
    ]),
    error: PropTypes.oneOfType([PropTypes.string, PropTypes.array]),
    helpContent: PropTypes.object,
    id: PropTypes.string,
    index: PropTypes.number,
    label: PropTypes.string,
    margin: PropTypes.string,
    name: PropTypes.string,
    onChange: PropTypes.func,
    rows: PropTypes.string,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  };

  constructor(props) {
    super(props);

    this.state = {
      help_showing: false,
    };
  }

  toggleHelp(e) {
    e.preventDefault();
    this.setState({ help_showing: !this.state.help_showing });
  }

  render() {
    return (
      <Row className={this.props.margin}>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>{this.props.label}</strong>
          </FormLabel>
          <br />
          <a
            href="#"
            name={this.props.name}
            data-index={this.props.index}
            onClick={this.toggleHelp}
          >
            Help
          </a>
        </Col>
        <Col md={9}>
          <FormControl
            as={this.props.as}
            rows={this.props.rows}
            data-index={this.props.index}
            id={this.props.id}
            type="text"
            name={this.props.name}
            onChange={event => {
              this.props.onChange(event.target.value);
            }}
            value={this.props.value}
            className={this.props.error ? "is-invalid" : ""}
          >
            {this.props.children}
          </FormControl>
          {this.props.error ? <Error error={this.props.error} /> : null}
          <HelpBox showing={this.state.help_showing}>
            {this.props.helpContent}
          </HelpBox>
        </Col>
      </Row>
    );
  }
}

export default DesignInput;

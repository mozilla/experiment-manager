/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import LinkMonitoring from ".";

storiesOf("Components/LinkMonitoring", module)
  .add("basic", () => (
    <div className="m-3">
      <LinkMonitoring monitoringDashboardUrl="https://grafana.telemetry.mozilla.org" />
    </div>
  ))
  .add("no link", () => (
    <div className="m-3">
      <LinkMonitoring monitoringDashboardUrl="" />
    </div>
  ));

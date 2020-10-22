/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { LocationProvider } from "@reach/router";
import { withLinks } from "@storybook/addon-links";
import AppLayoutWithSidebar from ".";

storiesOf("components/AppLayoutWithSidebar", module)
  .addDecorator((getStory) => <LocationProvider>{getStory()}</LocationProvider>)
  .addDecorator(withLinks)
  .add("basic", () => (
    <div data-testid="app">
      <AppLayoutWithSidebar>
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </div>
  ));
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import NotSet from ".";

storiesOf("Components/NotSet", module)
  .add("basic", () => <NotSet />)
  .add("custom copy", () => <NotSet copy="YOU'RE the one that's not set." />);

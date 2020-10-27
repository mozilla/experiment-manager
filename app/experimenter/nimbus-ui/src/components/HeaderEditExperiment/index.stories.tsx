/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import HeaderEditExperiment from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import AppLayout from "../AppLayout";

const { data } = mockExperimentQuery("demo-slug");

storiesOf("components/HeaderEditExperiment", module)
  .addDecorator(withLinks)
  .add("basic", () => (
    <AppLayout>
      <HeaderEditExperiment
        name={data!.name}
        slug={data!.slug}
        status={data!.status}
      />
    </AppLayout>
  ));

/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import { mockDirectoryExperiments } from "../../lib/mocks";
import DirectoryTable, {
  DirectoryCompleteTable,
  DirectoryDraftsTable,
  DirectoryLiveTable,
} from ".";

storiesOf("components/DirectoryTable", module)
  .addDecorator(withLinks)
  .add("basic", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperiments()}
      />
    );
  })
  .add("live", () => {
    return (
      <DirectoryLiveTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperiments()}
      />
    );
  })
  .add("complete", () => {
    return (
      <DirectoryCompleteTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperiments()}
      />
    );
  })
  .add("drafts", () => {
    return (
      <DirectoryDraftsTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperiments()}
      />
    );
  })
  .add("custom components", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperiments()}
        columns={[
          {
            label: "Testing column",
            component: ({ status }) => <td>Hello {status}</td>,
          },
        ]}
      />
    );
  })
  .add("no feature", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperiments([{ featureConfig: null }])}
      />
    );
  });

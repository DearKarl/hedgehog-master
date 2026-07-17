import { describe, expect, it } from "vitest";

import { getProjectName, projectIdentity } from "../src/index.js";

describe("M0 scaffold", () => {
  it("exports project identity", () => {
    expect(getProjectName()).toBe("Hedgehog Master Diagram IR");
    expect(projectIdentity).toMatchObject({
      module: "diagram-ir",
      repository: "hedgehog-master",
      scope: "v0.2"
    });
  });
});

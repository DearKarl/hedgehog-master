import { describe, expect, it } from "vitest";

import { getProjectName, projectIdentity } from "../src/index.js";

describe("M0 scaffold", () => {
  it("exports project identity", () => {
    expect(getProjectName()).toBe("Hedgehog One");
    expect(projectIdentity).toMatchObject({
      chineseName: "刺猬一号",
      repository: "hedgehog1",
      scope: "v0.1a"
    });
  });
});

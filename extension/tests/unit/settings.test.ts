import {describe, expect, it} from "vitest";
import {DEFAULT_SETTINGS, normalizeHostname, resolveSiteMode} from "../../src/shared/settings";

describe("site settings", () => {
  it("uses Adaptive by default", () => {
    expect(resolveSiteMode(DEFAULT_SETTINGS, "youtube.com")).toBe("adaptive");
  });

  it("uses exact-hostname overrides only", () => {
    const settings = {
      ...DEFAULT_SETTINGS,
      hostnameOverrides: {"youtube.com": "accent" as const},
    };
    expect(resolveSiteMode(settings, "youtube.com")).toBe("accent");
    expect(resolveSiteMode(settings, "music.youtube.com")).toBe("adaptive");
  });

  it("normalizes Unicode and trailing dots to lowercase ASCII", () => {
    expect(normalizeHostname("BÜCHER.example.")).toBe("xn--bcher-kva.example");
  });
});

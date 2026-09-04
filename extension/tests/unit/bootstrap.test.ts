import {afterEach, describe, expect, it} from "vitest";
import {applyBootstrap, BOOTSTRAP_STYLE_ID, removeBootstrap} from "../../src/content/bootstrap";
import {TOKYO_THEME} from "../helpers/themes";

afterEach(removeBootstrap);

describe("bootstrap", () => {
  it("uses only the cached canvas and color scheme", () => {
    applyBootstrap(TOKYO_THEME);
    const style = document.getElementById(BOOTSTRAP_STYLE_ID);
    expect(style?.textContent).toContain("#1a1b26");
    expect(style?.textContent).toContain("color-scheme: dark");
    expect(style?.textContent).toContain("@media print");
    expect(style?.textContent).not.toContain("img");
  });

  it("replaces rather than duplicates the style", () => {
    applyBootstrap(TOKYO_THEME);
    applyBootstrap({...TOKYO_THEME, mode: "light"});
    expect(document.querySelectorAll(`#${BOOTSTRAP_STYLE_ID}`)).toHaveLength(1);
  });
});

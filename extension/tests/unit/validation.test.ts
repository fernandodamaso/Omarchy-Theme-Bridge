import {describe, expect, it} from "vitest";
import {TOKYO_THEME} from "../helpers/themes";
import {isOmarchyTheme} from "../../src/shared/theme";
import {parseHostMessage} from "../../src/shared/native-messages";

describe("theme validation", () => {
  it("accepts a complete normalized theme", () => {
    expect(isOmarchyTheme(TOKYO_THEME)).toBe(true);
  });

  it("rejects a non-canonical generation", () => {
    expect(isOmarchyTheme({...TOKYO_THEME, generation: "tokyo"})).toBe(false);
  });

  it("rejects unbounded host payload fields", () => {
    expect(() => parseHostMessage({
      type: "theme.changed",
      theme: TOKYO_THEME,
      url: "https://example.com",
    })).toThrow();
  });
});

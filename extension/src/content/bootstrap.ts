import type {OmarchyTheme} from "../shared/theme";

export const BOOTSTRAP_STYLE_ID = "omarchy-theme-bridge-bootstrap";

export function applyBootstrap(theme: OmarchyTheme): void {
  const root = document.documentElement;
  if (!root) return;
  let style = document.getElementById(BOOTSTRAP_STYLE_ID) as HTMLStyleElement | null;
  if (!style) {
    style = document.createElement("style");
    style.id = BOOTSTRAP_STYLE_ID;
    root.prepend(style);
  }
  style.textContent = `
    html { background-color: ${theme.colors.canvas} !important; color-scheme: ${theme.mode}; }
    @media print { html { background-color: initial !important; color-scheme: normal; } }
  `;
}

export function removeBootstrap(): void {
  document.getElementById(BOOTSTRAP_STYLE_ID)?.remove();
}

import {describe, expect, it} from "vitest";
import {buildManifest} from "../../manifest.config";

const PUBLIC_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A";

describe("buildManifest", () => {
  it("declares only the approved permissions and ordinary web matches", () => {
    const manifest = buildManifest(PUBLIC_KEY);
    expect(manifest).toMatchObject({
      manifest_version: 3,
      name: "Omarchy Theme Bridge",
      version: "0.1.0",
      permissions: ["alarms", "nativeMessaging", "scripting", "storage"],
      host_permissions: ["http://*/*", "https://*/*"],
      background: {
        service_worker: "background/service-worker.js",
        type: "module",
      },
    });

    const permissions = manifest.permissions as string[];
    expect(permissions).not.toEqual(expect.arrayContaining([
      "bookmarks",
      "cookies",
      "downloads",
      "history",
      "identity",
    ]));
  });

  it("declares a document-start isolated content script in every eligible frame", () => {
    const manifest = buildManifest(PUBLIC_KEY) as {
      content_scripts: Array<Record<string, unknown>>;
    };

    expect(manifest.content_scripts[0]).toMatchObject({
      matches: ["http://*/*", "https://*/*"],
      js: ["content/content-script.js"],
      run_at: "document_start",
      all_frames: true,
      match_about_blank: true,
      match_origin_as_fallback: true,
    });
  });
});

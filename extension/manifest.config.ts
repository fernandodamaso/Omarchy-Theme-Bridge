export interface ManifestShape {
  manifest_version: 3;
  name: string;
  description: string;
  version: string;
  key: string;
  permissions: string[];
  host_permissions: string[];
  background: {
    service_worker: string;
    type: "module";
  };
  action: {
    default_title: string;
    default_popup: string;
  };
  options_ui: {
    page: string;
    open_in_tab: true;
  };
  content_scripts: Array<{
    matches: string[];
    js: string[];
    run_at: "document_start";
    all_frames: true;
    match_about_blank: true;
    match_origin_as_fallback: true;
  }>;
}

export function buildManifest(publicKey: string): ManifestShape {
  const key = publicKey.trim();
  if (!key) {
    throw new Error("Development public key is required");
  }

  return {
    manifest_version: 3,
    name: "Omarchy Theme Bridge",
    description: "Adapt website interfaces to the active Omarchy theme.",
    version: "0.1.0",
    key,
    permissions: ["alarms", "nativeMessaging", "scripting", "storage"],
    host_permissions: ["http://*/*", "https://*/*"],
    background: {
      service_worker: "background/service-worker.js",
      type: "module",
    },
    action: {
      default_title: "Omarchy Theme Bridge",
      default_popup: "popup/index.html",
    },
    options_ui: {
      page: "options/index.html",
      open_in_tab: true,
    },
    content_scripts: [
      {
        matches: ["http://*/*", "https://*/*"],
        js: ["content/content-script.js"],
        run_at: "document_start",
        all_frames: true,
        match_about_blank: true,
        match_origin_as_fallback: true,
      },
    ],
  };
}

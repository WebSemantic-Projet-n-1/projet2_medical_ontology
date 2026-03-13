/**
 * Content script Firefox — injecté sur les pages GO (QuickGO, AmiGO, OLS).
 * Extrait le GO ID, interroge le background, puis injecte un badge et un panneau de détails.
 */

const LOG = (...args) => console.log("[GO-Evo CS]", ...args);

const RUNTIME_API = (globalThis && (globalThis.browser || globalThis.chrome)) || undefined;

/**
 * Cross-browser wrapper for runtime.sendMessage.
 * Supports both callback-based (Chrome) and Promise-based (Firefox / polyfilled) forms.
 */
function sendMessageCompat(message) {
  return new Promise((resolve, reject) => {
    if (!RUNTIME_API?.runtime?.sendMessage) {
      reject(new Error("runtime messaging API is not available"));
      return;
    }

    // Firefox: browser.runtime.sendMessage is Promise-based and throws on callback argument
    if (globalThis.browser?.runtime) {
      globalThis.browser.runtime.sendMessage(message).then(resolve, reject);
      return;
    }

    // Chrome: callback-based API with lastError
    try {
      RUNTIME_API.runtime.sendMessage(message, (response) => {
        const lastError = RUNTIME_API.runtime?.lastError;
        if (lastError) {
          reject(new Error(lastError.message || String(lastError)));
        } else {
          resolve(response);
        }
      });
    } catch (err) {
      reject(err);
    }
  });
}

const GO_ID_REGEX = /GO:\d{7}/;
// OLS4 encodes terms as IRIs containing GO_XXXXXXX (underscore) rather than GO:XXXXXXX.
// Example URL: .../ols4/ontologies/go/classes/http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0006281
const GO_UNDERSCORE_REGEX = /GO_(\d{7})/;

const STATUS_LABELS = {
  stable: "Stable",
  modified: "Modifié",
  deprecated: "Déprécié",
  new: "Nouveau",
};

/**
 * Normalize status coming from the background/API to a known, safe value.
 * Falls back to "stable" if the value is missing or unrecognized.
 */
function normalizeStatus(status) {
  if (typeof status === "string" && Object.prototype.hasOwnProperty.call(STATUS_LABELS, status)) {
    return status;
  }
  return "stable";
}

/**
 * Validate and normalize a URL for use in href attributes.
 * Only http and https schemes are allowed; otherwise returns null.
 */
function normalizeReleaseNotesUrl(url) {
  if (!url || typeof url !== "string") {
    return null;
  }
  try {
    const base = (globalThis && globalThis.location && globalThis.location.href) ? globalThis.location.href : undefined;
    const parsed = new URL(url, base);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch (e) {
    // Invalid URL, fall through and return null
  }
  return null;
}

// ---------------------------------------------------------------------------
// 1. Extraction du GO ID
// ---------------------------------------------------------------------------

function extractGoId() {
  const href = globalThis.location.href;

  // Standard colon form — QuickGO, AmiGO, OLS3 all put GO:XXXXXXX directly in the URL.
  const urlMatch = GO_ID_REGEX.exec(href);
  if (urlMatch) {
    LOG(`GO ID found in URL (colon form): ${urlMatch[0]}`);
    return urlMatch[0];
  }

  // OLS4 embeds the term as an IRI in the URL path: …/obo/GO_XXXXXXX (underscore).
  // The digits and underscore are never percent-encoded, so matching the raw href works.
  const ols4Match = GO_UNDERSCORE_REGEX.exec(href);
  if (ols4Match) {
    const goId = `GO:${ols4Match[1]}`;
    LOG(`GO ID found in OLS4 URL (underscore IRI form): ${goId}`);
    return goId;
  }

  // DOM fallback — catches GO:XXXXXXX displayed in page headings on all sites.
  const heading = document.querySelector("h1, h2, .ontology-detail-title");
  if (heading) {
    const domMatch = GO_ID_REGEX.exec(heading.textContent);
    if (domMatch) {
      LOG(`GO ID found in DOM heading: ${domMatch[0]}`);
      return domMatch[0];
    }
  }

  LOG("No GO ID found on this page");
  return null;
}

// ---------------------------------------------------------------------------
// 2. Badge injection
// ---------------------------------------------------------------------------

function injectBadge(data) {
  if (document.querySelector(".go-evo-badge")) {
    LOG("Badge already present, skipping injection");
    return;
  }

  const safeStatus = normalizeStatus(data.status);
  LOG(`Injecting badge: status=${safeStatus}, go_id=${data.go_id}, label=${data.label}`);

  const badge = document.createElement("button");
  badge.type = "button";
  badge.className = `go-evo-badge go-evo-${safeStatus}`;
  badge.textContent = STATUS_LABELS[safeStatus];
  badge.title = `${data.go_id} — ${data.label}`;

  const details = buildDetailsPanel(data);
  const detailsId = `go-evo-details-${data.go_id}`;
  if (!details.id) {
    details.id = detailsId;
  }
  badge.setAttribute("aria-controls", details.id);
  badge.setAttribute("aria-expanded", details.style.display === "none" ? "false" : "true");

  document.body.appendChild(badge);
  document.body.appendChild(details);

  badge.addEventListener("click", () => {
    const isHidden = details.style.display === "none";
    details.style.display = isHidden ? "flex" : "none";
    badge.setAttribute("aria-expanded", isHidden ? "true" : "false");
  });

  LOG("Badge and details panel injected successfully");
}

// ---------------------------------------------------------------------------
// 3. Detailed comparison panel
// ---------------------------------------------------------------------------

function buildDetailsPanel(d) {
  const panel = document.createElement("div");
  panel.className = "go-evo-details";
  panel.style.display = "none";

  const showTree = (d.hierarchy_old || d.hierarchy_new) &&
    d.hierarchy_old !== d.hierarchy_new;

  const safeReleaseNotesUrl = normalizeReleaseNotesUrl(d.release_notes_url);

  panel.innerHTML = `
    <div class="go-evo-details-header">
      <h3>${esc(d.go_id)} — ${esc(d.label)}</h3>
      <button type="button" class="go-evo-close" aria-label="Fermer le panneau de détails">&times;</button>
    </div>
    <div class="go-evo-details-body">
      <div class="go-evo-col">
        <h4>Ancienne définition</h4>
        <p>${esc(d.definition_old) || "<em>N/A</em>"}</p>
      </div>
      <div class="go-evo-col">
        <h4>Nouvelle définition</h4>
        <p>${esc(d.definition_new) || "<em>N/A</em>"}</p>
      </div>
    </div>
    ${showTree ? buildTreeComparison(d.hierarchy_old, d.hierarchy_new) : ""}
    <div class="go-evo-details-footer">
      <span>Statut : <strong>${esc(STATUS_LABELS[d.status] || d.status)}</strong></span>
      ${d.change_date ? `<span>Date : ${esc(d.change_date)}</span>` : ""}
      ${safeReleaseNotesUrl ? `<a href="${esc(safeReleaseNotesUrl)}" target="_blank" rel="noopener">Release notes</a>` : ""}
    </div>
  `;

  const closeButton = panel.querySelector(".go-evo-close");
  if (closeButton) {
    closeButton.addEventListener("click", () => {
      panel.style.display = "none";
      const trigger = panel.previousElementSibling;
      if (trigger && trigger.hasAttribute("aria-expanded")) {
        trigger.setAttribute("aria-expanded", "false");
      }
    });
  }

  return panel;
}

// ---------------------------------------------------------------------------
// 3b. Comparative hierarchy tree
// ---------------------------------------------------------------------------

function parseHierarchy(str) {
  if (!str) return [];
  return str.split(" > ").map((s) => s.trim()).filter(Boolean);
}

function buildTreeComparison(oldStr, newStr) {
  const oldNodes = parseHierarchy(oldStr);
  const newNodes = parseHierarchy(newStr);

  const oldSet = new Set(oldNodes);
  const newSet = new Set(newNodes);

  let firstDiffIdx = 0;
  while (
    firstDiffIdx < oldNodes.length &&
    firstDiffIdx < newNodes.length &&
    oldNodes[firstDiffIdx] === newNodes[firstDiffIdx]
  ) {
    firstDiffIdx++;
  }

  return `
    <div class="go-evo-tree-section">
      <h4>Arbre hiérarchique comparatif</h4>
      <div class="go-evo-tree-wrap">
        <div class="go-evo-tree-col">
          <span class="go-evo-tree-label">Ancienne version</span>
          ${renderTree(oldNodes, newSet, firstDiffIdx, "removed")}
        </div>
        <div class="go-evo-tree-col">
          <span class="go-evo-tree-label">Nouvelle version</span>
          ${renderTree(newNodes, oldSet, firstDiffIdx, "added")}
        </div>
      </div>
    </div>
  `;
}

function renderTree(nodes, otherSet, firstDiffIdx, diffClass) {
  if (!nodes.length) return '<div class="go-evo-tree-empty">N/A</div>';

  return nodes
    .map((node, i) => {
      let cls = "go-evo-tree-node";
      if (i >= firstDiffIdx && !otherSet.has(node)) {
        cls += ` go-evo-tree-${diffClass}`;
      } else if (i >= firstDiffIdx) {
        cls += " go-evo-tree-moved";
      }
      const indent = i * 18;
      return `<div class="${cls}" style="padding-left:${indent + 6}px">${esc(node)}</div>`;
    })
    .join("");
}

function esc(str) {
  if (!str) return "";
  const el = document.createElement("span");
  el.textContent = str;
  return el.innerHTML;
}

// ---------------------------------------------------------------------------
// 4. Main
// ---------------------------------------------------------------------------

(function main() {
  LOG(`Content script loaded on ${globalThis.location.href}`);

  const goId = extractGoId();
  if (!goId) {
    LOG("Aborting — no GO ID detected");
    return;
  }

  LOG(`Sending getTermDiff request for ${goId}`);

  if (!RUNTIME_API || !RUNTIME_API.runtime || typeof RUNTIME_API.runtime.sendMessage !== "function") {
    LOG("Aborting — runtime messaging API is not available");
    return;
  }

  sendMessageCompat({ action: "getTermDiff", goId })
    .then((response) => {
      LOG("Response from background:", JSON.stringify(response));

      if (response?.error) {
        LOG(`API error: ${response.error}`);
        return;
      }
      if (response?.notFound) {
        LOG(`Term ${goId} not found in API (404)`);
        return;
      }
      if (response?.status) {
        injectBadge(response);
      } else {
        LOG("Unexpected response format — no status field");
      }
    })
    .catch((err) => LOG("Message error:", err));
})();

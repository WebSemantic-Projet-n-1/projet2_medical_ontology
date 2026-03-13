/**
 * Content script Firefox — injecté sur les pages GO (QuickGO, AmiGO, OLS).
 * Extrait le GO ID, interroge le background, puis injecte un badge et un panneau de détails.
 */

const LOG = (...args) => console.log("[GO-Evo CS]", ...args);

const GO_ID_REGEX = /GO:\d{7}/;

const STATUS_LABELS = {
  stable: "Stable",
  modified: "Modifié",
  deprecated: "Déprécié",
  new: "Nouveau",
};

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
  const urlMatch = GO_ID_REGEX.exec(globalThis.location.href);
  if (urlMatch) {
    LOG(`GO ID found in URL: ${urlMatch[0]}`);
    return urlMatch[0];
  }

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

  LOG(`Injecting badge: status=${data.status}, go_id=${data.go_id}, label=${data.label}`);

  const badge = document.createElement("div");
  badge.className = `go-evo-badge go-evo-${data.status}`;
  badge.textContent = STATUS_LABELS[data.status] || data.status;
  badge.title = `${data.go_id} — ${data.label}`;
  document.body.appendChild(badge);

  const details = buildDetailsPanel(data);
  document.body.appendChild(details);

  badge.addEventListener("click", () => {
    details.style.display = details.style.display === "none" ? "flex" : "none";
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
      <button class="go-evo-close">&times;</button>
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

  panel.querySelector(".go-evo-close").addEventListener("click", () => {
    panel.style.display = "none";
  });

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
      const connector = i > 0
        ? `<span class="go-evo-tree-branch" style="width:${indent}px"></span>`
        : "";
      return `<div class="${cls}" style="padding-left:${indent + 6}px">
        ${connector}${esc(node)}
      </div>`;
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

  browser.runtime
    .sendMessage({ action: "getTermDiff", goId })
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

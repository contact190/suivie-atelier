/**
 * SuiviPRO v2.0 - Étape 1 : Réglages des Types de Fenêtres & Rôles
 * Liste Pliante & Dépliante (Accordéon Interactif)
 */

let currentSettings = {
  roles: [],
  joinery_types: []
};

// Ensemble des IDs des modèles actuellement dépliés
const openItemIds = new Set();
let searchQuery = "";

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  
  // Par défaut, déplier le premier élément pour inviter à la modification
  if (currentSettings.joinery_types.length > 0) {
    openItemIds.add(currentSettings.joinery_types[0].id);
    renderTypesAccordion();
  }
});

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    currentSettings = await res.json();
    renderSettingsView();
  } catch (err) {
    console.error('Erreur chargement réglages:', err);
    showToast('Erreur de connexion au serveur', 'warning');
  }
}

function renderSettingsView() {
  renderRolesLegend();
  renderTypesAccordion();
}

// 1. Barre de légende des 5 rôles clés
function renderRolesLegend() {
  const container = document.getElementById('rolesLegendBar');
  if (!container) return;

  container.innerHTML = currentSettings.roles.map(r => `
    <div class="role-legend-item">
      <div class="role-color-dot" style="background-color: ${r.color};"></div>
      <span>${r.label}</span>
      <span style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">(${r.default_pct}%)</span>
    </div>
  `).join('');
}

// 2. Rendu de la Liste Pliante & Dépliante
function renderTypesAccordion() {
  const container = document.getElementById('typesAccordionContainer');
  const countBadge = document.getElementById('typesCountBadge');
  if (!container) return;

  // Filtrage par recherche
  const filtered = currentSettings.joinery_types.filter(t => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (t.label && t.label.toLowerCase().includes(q)) || 
           (t.description && t.description.toLowerCase().includes(q));
  });

  if (countBadge) {
    countBadge.textContent = `${filtered.length} modèle${filtered.length > 1 ? 's' : ''}`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="background: #FFFFFF; border: 1px dashed var(--border-subtle); border-radius: 12px; text-align: center; padding: 3rem; color: var(--text-muted);">
        ${searchQuery ? `Aucun modèle ne correspond à la recherche "<strong>${escapeHtml(searchQuery)}</strong>".` : 'Aucun modèle configuré.'}
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(t => renderAccordionItem(t)).join('');
}

function renderAccordionItem(item) {
  const roles = currentSettings.roles;
  const ratios = item.ratios || {};
  const totalMin = parseFloat(item.temps_moyen_min || 60);
  const isOpen = openItemIds.has(item.id);

  // Somme des pourcentages
  const sumPct = roles.reduce((acc, r) => acc + (parseFloat(ratios[r.id]) || 0), 0);
  const isValid100 = Math.abs(sumPct - 100) < 0.1;

  return `
    <div class="accordion-item ${isOpen ? 'is-open' : ''}" id="accordion-${item.id}">
      <!-- En-tête cliquable pour plier / déplier -->
      <div class="accordion-header" onclick="toggleAccordionItem('${item.id}')">
        <div class="accordion-title-box">
          <div class="chevron-icon">▶</div>
          <div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A;">${item.label}</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 1px;">
              ${item.description || 'Menuiserie standard atelier'}
            </div>
          </div>
        </div>

        <!-- Aperçu rapide replié : Mini-barre, badge temps et validité 100% -->
        <div class="accordion-preview-box">
          <!-- Mini barre visuelle de prévisualisation -->
          <div style="width: 140px; height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden; display: flex;" title="Aperçu de la répartition">
            ${roles.map(r => {
              const pct = parseFloat(ratios[r.id] || 0);
              return `<div style="width: ${pct}%; height: 100%; background-color: ${r.color};"></div>`;
            }).join('')}
          </div>

          <div class="time-badge">
            ⏱️ ${totalMin} min
          </div>

          <span class="sum-badge ${isValid100 ? 'valid' : 'invalid'}" style="font-size: 0.75rem; padding: 3px 8px;">
            ${isValid100 ? '100%' : `${Math.round(sumPct)}%`}
          </span>
        </div>
      </div>

      <!-- Contenu Déplié : Édition complète des temps et pourcentages -->
      <div class="accordion-content">
        <!-- Ligne 1 : Ajustement du Temps Moyen Total -->
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; background: #F8FAFC; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem 1.25rem;">
          <div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #0F172A;">
              Temps Moyen Théorique Total :
            </div>
            <div style="font-size: 0.775rem; color: var(--text-secondary);">
              Temps global de référence alloué à la fabrication de ce modèle
            </div>
          </div>

          <div class="time-input-box" onclick="event.stopPropagation()">
            <input type="number" step="0.5" min="5" max="999" 
                   class="time-input-field" 
                   value="${totalMin}" 
                   id="time-${item.id}"
                   oninput="handleRealtimeRecalc('${item.id}')" />
            <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted);">minutes</span>
          </div>
        </div>

        <!-- Ligne 2 : Grande Barre Visuelle des Proportions -->
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">
              Ventilation par Rôle Atelier :
            </span>
            <span class="sum-badge ${isValid100 ? 'valid' : 'invalid'}" id="badge-${item.id}">
              ${isValid100 ? '✅ Total : 100%' : `⚠️ Total : ${Math.round(sumPct)}% (écart ${sumPct > 100 ? '+' : ''}${Math.round(sumPct - 100)}%)`}
            </span>
          </div>

          <div class="stacked-bar-container" id="stacked-bar-${item.id}">
            ${roles.map(r => {
              const pct = parseFloat(ratios[r.id] || 0);
              return `<div class="stacked-segment" style="width: ${pct}%; background-color: ${r.color};" title="${r.label}: ${pct}%"></div>`;
            }).join('')}
          </div>
        </div>

        <!-- Ligne 3 : Les 5 Rôles Éditables avec Calcul Immédiat des Minutes -->
        <div class="roles-pct-grid" onclick="event.stopPropagation()">
          ${roles.map(r => {
            const pct = parseFloat(ratios[r.id] || 0);
            const allocatedMin = Math.round((totalMin * pct) / 100 * 10) / 10;
            return `
              <div class="role-pct-box" style="--role-color: ${r.color};">
                <span class="role-pct-label" title="${r.label}">${r.label}</span>
                <div class="role-pct-input-wrap">
                  <input type="number" min="0" max="100" 
                         class="role-pct-input" 
                         value="${pct}" 
                         id="pct-${item.id}-${r.id}"
                         data-role="${r.id}"
                         oninput="handleRealtimeRecalc('${item.id}')" />
                  <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted);">%</span>
                </div>
                <div class="role-calc-min" id="calc-${item.id}-${r.id}">${allocatedMin} min</div>
              </div>
            `;
          }).join('')}
        </div>

        <!-- Ligne 4 : Boutons d'Action (Enregistrer / Supprimer) -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 1rem;" onclick="event.stopPropagation()">
          <button class="btn btn-danger-outline" style="padding: 0.45rem 0.85rem; font-size: 0.8rem;" 
                  onclick="deleteJoineryType('${item.id}', '${item.label}')">
            🗑️ Supprimer ce modèle
          </button>

          <button class="btn btn-primary" style="padding: 0.55rem 1.35rem;" 
                  id="save-btn-${item.id}"
                  onclick="saveTypeChanges('${item.id}')">
            💾 Enregistrer ce modèle
          </button>
        </div>
      </div>
    </div>
  `;
}

// Bascule plié / déplié pour un modèle spécifique
function toggleAccordionItem(typeId) {
  if (openItemIds.has(typeId)) {
    openItemIds.delete(typeId);
  } else {
    openItemIds.add(typeId);
  }
  renderTypesAccordion();
}

// Tout déplier
function expandAllItems() {
  currentSettings.joinery_types.forEach(t => openItemIds.add(t.id));
  renderTypesAccordion();
}

// Tout replier
function collapseAllItems() {
  openItemIds.clear();
  renderTypesAccordion();
}

// Filtrage par recherche
function handleSearchInput(value) {
  searchQuery = value.trim();
  renderTypesAccordion();
}

// Recalcul en direct dès la frappe
function handleRealtimeRecalc(typeId) {
  const timeInput = document.getElementById(`time-${typeId}`);
  if (!timeInput) return;

  const totalMin = parseFloat(timeInput.value) || 0;
  let sumPct = 0;
  const roles = currentSettings.roles;
  const newRatios = {};

  roles.forEach(r => {
    const input = document.getElementById(`pct-${typeId}-${r.id}`);
    const pct = parseFloat(input ? input.value : 0) || 0;
    newRatios[r.id] = pct;
    sumPct += pct;

    const calcEl = document.getElementById(`calc-${typeId}-${r.id}`);
    if (calcEl) {
      const allocated = Math.round((totalMin * pct) / 100 * 10) / 10;
      calcEl.textContent = `${allocated} min`;
    }
  });

  // Mise à jour de la grande barre empilée
  const stackedBar = document.getElementById(`stacked-bar-${typeId}`);
  if (stackedBar) {
    stackedBar.innerHTML = roles.map(r => `
      <div class="stacked-segment" style="width: ${newRatios[r.id]}%; background-color: ${r.color};" title="${r.label}: ${newRatios[r.id]}%"></div>
    `).join('');
  }

  // Mise à jour du badge de somme
  const badge = document.getElementById(`badge-${typeId}`);
  if (badge) {
    const isValid100 = Math.abs(sumPct - 100) < 0.1;
    badge.className = `sum-badge ${isValid100 ? 'valid' : 'invalid'}`;
    badge.textContent = isValid100 
      ? '✅ Total : 100%' 
      : `⚠️ Total : ${Math.round(sumPct)}% (écart ${sumPct > 100 ? '+' : ''}${Math.round(sumPct - 100)}%)`;
  }
}

// Sauvegarde des modifications vers l'API
async function saveTypeChanges(typeId) {
  const timeInput = document.getElementById(`time-${typeId}`);
  if (!timeInput) return;

  const totalMin = parseFloat(timeInput.value) || 0;
  const ratios = {};
  let sumPct = 0;

  currentSettings.roles.forEach(r => {
    const input = document.getElementById(`pct-${typeId}-${r.id}`);
    const val = parseFloat(input ? input.value : 0) || 0;
    ratios[r.id] = val;
    sumPct += val;
  });

  if (Math.abs(sumPct - 100) > 0.1) {
    const confirmSave = confirm(`Attention : La somme des pourcentages est de ${Math.round(sumPct)}% (doit être idéalement de 100%). Voulez-vous quand même enregistrer ?`);
    if (!confirmSave) return;
  }

  try {
    const saveBtn = document.getElementById(`save-btn-${typeId}`);
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = 'Enregistrement...';
    }

    const res = await fetch(`/api/settings/types/${typeId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        temps_moyen_min: totalMin,
        ratios: ratios
      })
    });

    if (res.ok) {
      showToast('Modifications enregistrées avec succès', 'success');
      await loadSettings();
    } else {
      showToast('Erreur lors de l’enregistrement', 'warning');
    }
  } catch (err) {
    console.error(err);
    showToast('Erreur réseau lors de la sauvegarde', 'warning');
  }
}

// Suppression d'un type
async function deleteJoineryType(typeId, label) {
  if (!confirm(`Confirmez-vous la suppression du modèle "${label}" ?`)) return;

  try {
    const res = await fetch(`/api/settings/types/${typeId}`, { method: 'DELETE' });
    if (res.ok) {
      openItemIds.delete(typeId);
      showToast(`Modèle "${label}" supprimé`, 'success');
      await loadSettings();
    }
  } catch (err) {
    showToast('Erreur lors de la suppression', 'warning');
  }
}

// Modal d'ajout d'un nouveau modèle
function openAddTypeModal() {
  const modal = document.getElementById('addTypeModal');
  if (modal) modal.classList.add('active');
}

function closeAddTypeModal() {
  const modal = document.getElementById('addTypeModal');
  if (modal) modal.classList.remove('active');
}

async function submitNewType() {
  const labelInput = document.getElementById('new_type_label');
  const descInput = document.getElementById('new_type_desc');
  const timeInput = document.getElementById('new_type_time');

  const label = labelInput ? labelInput.value.trim() : '';
  const desc = descInput ? descInput.value.trim() : '';
  const time = parseFloat(timeInput ? timeInput.value : 60) || 60;

  if (!label) {
    showToast('Veuillez renseigner un nom pour le type de fenêtre', 'warning');
    return;
  }

  const payload = {
    label: label,
    description: desc || 'Menuiserie personnalisée',
    temps_moyen_min: time
  };

  try {
    const res = await fetch('/api/settings/types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const created = await res.json();
      openItemIds.add(created.id); // Déplier automatiquement le nouvel élément
      showToast(`Nouveau modèle "${label}" ajouté`, 'success');
      closeAddTypeModal();
      labelInput.value = '';
      if (descInput) descInput.value = '';
      await loadSettings();
    }
  } catch (err) {
    showToast('Erreur lors de l’ajout du modèle', 'warning');
  }
}

// Réinitialisation aux réglages d'usine
async function resetFactorySettings() {
  if (!confirm('Voulez-vous rétablir les réglages d’usine par défaut pour l’ensemble des types de fenêtres ?')) return;

  try {
    const res = await fetch('/api/settings/reset', { method: 'POST' });
    if (res.ok) {
      showToast('Réglages d’usine rétablis avec succès', 'success');
      await loadSettings();
    }
  } catch (err) {
    showToast('Erreur lors de la réinitialisation', 'warning');
  }
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-msg toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✅' : '⚠️'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

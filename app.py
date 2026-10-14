"""
SuiviPRO - Réglages Atelier (100% Python Pur avec NiceGUI)
Sous-onglets :
  1. 🪟 Modèles de Menuiseries & Temps Cibles (32 modèles réels avec rôles libres)
  2. 🏗️ Organisation d'Atelier & Tables (Tables multi-rôles avec employé dédié par rôle)
  3. 👥 Employés d'Atelier (Gestion des opérateurs, spécialités, contacts et affectations)
"""

import sys
from datetime import datetime
from typing import Dict, Any, List

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from nicegui import ui, app
from settings_manager import settings_mgr

# Styles globaux (Design épuré fond blanc et typographie moderne)
ui.add_head_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    :root {
        --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }
    
    body {
        font-family: var(--font-sans);
        background-color: #F8FAFC !important;
        color: #0F172A;
    }
    
    .q-expansion-item {
        border-radius: 12px !important;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .q-expansion-item:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
    }
    .q-expansion-item--expanded {
        border-color: #3B82F6 !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.09) !important;
    }
    .q-tab {
        font-family: var(--font-sans) !important;
        font-weight: 700 !important;
        text-transform: none !important;
        font-size: 0.875rem !important;
    }
    .q-item__label {
        font-family: var(--font-sans) !important;
    }
    .font-mono {
        font-family: var(--font-mono) !important;
    }
</style>
<script>
window.suiviCam = {
    streams: {},
    async start(videoId, statusId) {
        let video = document.getElementById(videoId);
        let status = statusId ? document.getElementById(statusId) : null;
        
        // Attendre que l'élément soit inséré dans le DOM (transition modale Quasar/NiceGUI)
        if (!video) {
            for (let i = 0; i < 6; i++) {
                await new Promise(r => setTimeout(r, 100));
                video = document.getElementById(videoId);
                if (video) break;
            }
        }
        if (statusId) status = document.getElementById(statusId);

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            if (status) status.innerHTML = "<span style='color:#D97706; font-weight:bold;'>⚠️ Caméra inaccessible (utilisez localhost ou HTTPS)</span>";
            return false;
        }

        try {
            if (this.streams[videoId]) {
                try { this.streams[videoId].getTracks().forEach(t => t.stop()); } catch(e){}
            }
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            });
            this.streams[videoId] = stream;
            if (video) {
                video.setAttribute('autoplay', '');
                video.setAttribute('playsinline', '');
                video.setAttribute('webkit-playsinline', '');
                video.muted = true;
                video.srcObject = stream;
                try {
                    await video.play();
                } catch(playErr) {
                    console.warn("Lecture vidéo automatique en attente d'interaction :", playErr);
                }
                if (status) status.innerHTML = "<span style='color:#10B981; font-weight:bold;'>🟢 Caméra Active</span>";
            }
            return true;
        } catch (err) {
            console.error("Camera access error:", err);
            let msg = "⚠️ Caméra bloquée : autorisez l'accès dans votre navigateur";
            if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                msg = "⚠️ Aucune caméra détectée sur cet appareil";
            } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
                msg = "⚠️ Caméra déjà occupée par une autre application";
            } else if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                msg = "⚠️ Accès refusé : cliquez sur l'icône caméra de la barre d'adresse";
            }
            if (status) status.innerHTML = `<span style='color:#EF4444; font-weight:bold;'>${msg}</span>`;
            return false;
        }
    },
    stop(videoId) {
        if (this.streams[videoId]) {
            try { this.streams[videoId].getTracks().forEach(t => t.stop()); } catch(e){}
            delete this.streams[videoId];
        }
    },
    capture(videoId) {
        const video = document.getElementById(videoId);
        if (!video) return null;
        const w = video.videoWidth || video.clientWidth || 480;
        const h = video.videoHeight || video.clientHeight || 360;
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, w, h);
        return canvas.toDataURL('image/jpeg', 0.85);
    },
    playChime() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.type = 'sine';
            o.connect(g);
            g.connect(ctx.destination);
            o.frequency.setValueAtTime(587.33, ctx.currentTime);
            o.frequency.setValueAtTime(880, ctx.currentTime + 0.12);
            g.gain.setValueAtTime(0.25, ctx.currentTime);
            g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
            o.start();
            o.stop(ctx.currentTime + 0.45);
        } catch(e) {}
    }
};
</script>

""", shared=True)

# État global de l'interface
state = {
    "active_main_tab": "tab_models",
    "search": "",
    "selected_category": "ALL",
    "expansions": {}
}

CATEGORIES = [
    {"id": "ALL", "label": "Tous les modèles", "icon": "apps"},
    {"id": "CAT-F - Coulissant", "label": "Coulissants (CAT-F)", "icon": "view_week"},
    {"id": "CAT-F - Ouvrant", "label": "Ouvrants & Portes (CAT-F)", "icon": "door_front"},
    {"id": "CAT-F - Fixe", "label": "Fixes & Précadres (CAT-F)", "icon": "crop_free"},
    {"id": "CAT-Special - Garde Corps", "label": "Spécial / Garde-corps", "icon": "shield"}
]

ROLE_COLORS = [
    "#3B82F6", "#8B5CF6", "#F59E0B", "#06B6D4", "#10B981", 
    "#EC4899", "#6366F1", "#F97316", "#14B8A6", "#64748B"
]

# =========================================================================
# SOUS-ONGLET 1 : MODÈLES DE FENÊTRES & TEMPS CIBLES (CATALOGUE 32 MODÈLES)
# =========================================================================

@ui.refreshable
def render_roles_legend():
    """Barre de légende des rôles atelier"""
    roles = settings_mgr.get_roles()
    with ui.row().classes('w-full bg-white border border-slate-200 rounded-xl p-3 px-4 items-center justify-between shadow-2xs mb-4 flex-wrap gap-3'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('tune', size='xs').classes('text-slate-400')
            ui.label(f'Postes de production ({len(roles)} rôles) :').classes('text-xs font-bold text-slate-500 uppercase tracking-wider')
        
        with ui.row().classes('items-center gap-4 flex-wrap'):
            for role in roles:
                with ui.row().classes('items-center gap-1.5'):
                    ui.html(f'<div style="width: 10px; height: 10px; border-radius: 50%; background-color: {role["color"]};"></div>')
                    ui.label(role["label"]).classes('text-xs font-semibold text-slate-700')
                    ui.label(f'({role.get("default_pct", 10)}%)').classes('text-xs text-slate-400 font-mono')

@ui.refreshable
def render_category_tabs():
    """Filtres par catégories pour les modèles de fenêtres"""
    settings = settings_mgr.get_settings()
    all_types = settings["joinery_types"]

    with ui.row().classes('w-full items-center gap-2 mb-4 flex-wrap'):
        for cat in CATEGORIES:
            cid = cat["id"]
            if cid == "ALL":
                count = len(all_types)
            else:
                count = len([t for t in all_types if t.get("categorie") == cid])
            
            is_active = (state["selected_category"] == cid)
            btn_classes = (
                'font-bold text-xs px-3 py-1.5 rounded-lg border transition-all ' + 
                ('bg-blue-600 text-white border-blue-600 shadow-xs' if is_active else 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50')
            )

            def make_click_cat(c_val=cid):
                def on_click():
                    state["selected_category"] = c_val
                    render_category_tabs.refresh()
                    render_accordion_list.refresh()
                return on_click

            ui.button(f"{cat['label']} ({count})", on_click=make_click_cat()).props('flat dense no-caps').classes(btn_classes)

@ui.refreshable
def render_accordion_list():
    """Rendu de la liste pliante / dépliante des modèles"""
    settings = settings_mgr.get_settings()
    items: List[Dict[str, Any]] = settings["joinery_types"]
    roles = settings_mgr.get_roles()
    
    if state["selected_category"] != "ALL":
        items = [t for t in items if t.get("categorie") == state["selected_category"]]

    query = state["search"].lower().strip()
    if query:
        items = [
            t for t in items if 
            query in t["label"].lower() or 
            query in t.get("gamme", "").lower() or 
            query in t.get("categorie", "").lower() or 
            query in t.get("description", "").lower()
        ]

    with ui.row().classes('w-full items-center justify-between mb-3 flex-wrap gap-2'):
        with ui.row().classes('items-center gap-2'):
            ui.label(f'{len(items)} modèle(s) affiché(s)').classes('text-xs font-bold text-slate-700 bg-white border border-slate-200 px-3 py-1 rounded-full shadow-2xs')
            if query:
                ui.label(f'Recherche : "{query}"').classes('text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200')
        
        with ui.row().classes('items-center gap-2'):
            ui.button('📂 Tout déplier', on_click=expand_all).props('flat dense size=sm').classes('text-slate-600 hover:text-blue-600 font-semibold')
            ui.button('📁 Tout replier', on_click=collapse_all).props('flat dense size=sm').classes('text-slate-600 hover:text-blue-600 font-semibold')

    if not items:
        with ui.card().classes('w-full bg-white border border-dashed border-slate-300 p-8 text-center items-center justify-center'):
            ui.icon('search_off', size='48px').classes('text-slate-300 mb-2')
            ui.label('Aucun modèle ne correspond à vos filtres.').classes('text-slate-500 font-medium')
        return

    state["expansions"].clear()
    for item in items:
        render_item_accordion(item, roles)

def render_item_accordion(item: Dict[str, Any], all_roles: List[Dict[str, Any]]):
    """Rendu d'un modèle sous forme d'accordéon pliant/dépliant avec sélection libre des rôles"""
    item_id = item["id"]
    total_time = float(item.get("temps_moyen_min", 60.0))
    ratios = dict(item.get("ratios", {}))
    has_joint = item.get("has_joint_vitrage", True)
    comp_count = item.get("composants_count", 15)
    gamme = item.get("gamme", "")
    categorie = item.get("categorie", "CAT-F")

    # 1. Rôles actifs pour ce modèle spécifique
    active_role_ids = [r_id for r_id in ratios.keys() if any(r["id"] == r_id for r in all_roles)]
    if not active_role_ids and all_roles:
        active_roles = list(all_roles[:5])
        for r in active_roles:
            ratios[r["id"]] = r.get("default_pct", 20.0)
    else:
        active_roles = [r for r in all_roles if r["id"] in active_role_ids]

    # 2. Rôles disponibles à ajouter
    active_ids_set = {r["id"] for r in active_roles}
    available_roles_to_add = [r for r in all_roles if r["id"] not in active_ids_set]

    # Somme des pourcentages actuelle pour ce modèle
    current_sum = sum(float(ratios.get(r["id"], 0.0)) for r in active_roles)
    is_valid = abs(current_sum - 100.0) < 0.1

    fields = {
        "time": total_time,
        "active_roles": active_roles,
        "min_labels": {},
        "pct_inputs": {}
    }

    with ui.expansion().classes('w-full') as exp:
        state["expansions"][item_id] = exp

        with exp.add_slot('header'):
            with ui.row().classes('w-full items-center justify-between pr-3 flex-wrap gap-2'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('dashboard', size='xs').classes('text-blue-600')
                    with ui.column().classes('gap-0'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(item['label']).classes('text-sm font-bold text-slate-900')
                            if gamme:
                                ui.label(f'Gamme : {gamme}').classes('text-2xs font-semibold bg-slate-100 text-slate-600 border border-slate-200 px-2 py-0.5 rounded')
                            if categorie:
                                cat_clean = categorie.replace('CAT-F - ', '')
                                ui.label(cat_clean).classes('text-2xs font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded')
                        
                        with ui.row().classes('items-center gap-2 mt-0.5'):
                            if has_joint:
                                ui.label('☑️ Comporte Joint Vitrage').classes('text-2xs text-emerald-700 font-medium')
                            ui.label(f'• {comp_count} composants').classes('text-2xs text-slate-400')
                            ui.label(f'• {len(active_roles)} poste(s)').classes('text-2xs font-semibold text-blue-600')
                
                with ui.row().classes('items-center gap-3'):
                    with ui.row().classes('w-28 h-2 rounded-full overflow-hidden bg-slate-200 gap-0 no-wrap shadow-2xs'):
                        for r in active_roles:
                            p = float(ratios.get(r["id"], 0.0))
                            ui.html(f'<div style="width: {p}%; height: 100%; background-color: {r["color"]};"></div>')

                    ui.label(f'⏱️ {total_time:.0f} min').classes('text-xs font-bold font-mono bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded')

                    if is_valid:
                        ui.label('100%').classes('text-xs font-bold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded')
                    else:
                        ui.label(f'{current_sum:.0f}%').classes('text-xs font-bold font-mono bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded')

        with ui.column().classes('w-full p-4 pt-3 gap-3 bg-slate-50/70 border-t border-slate-200'):
            # Ligne 1 : Temps moyen total
            with ui.row().classes('w-full bg-white border border-slate-200 rounded-lg p-3 px-4 items-center justify-between flex-wrap gap-2'):
                with ui.column().classes('gap-0'):
                    ui.label('Temps Moyen Théorique Total de Fabrication :').classes('text-xs font-bold text-slate-800')
                    ui.label(f'Référentiel alloué pour la fabrication complète de ce modèle ({gamme})').classes('text-2xs text-slate-500')
                
                with ui.row().classes('items-center gap-2'):
                    time_input = ui.number(
                        value=total_time, 
                        min=5, 
                        max=999, 
                        step=5, 
                        format='%.0f'
                    ).props('outlined dense suffix="min"').classes('w-32 font-mono text-sm font-bold bg-white')
                    fields["time_input"] = time_input

            # Ligne 2 : En-tête de ventilation + Ajout de rôles
            with ui.row().classes('w-full items-center justify-between flex-wrap gap-2 mt-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.label(f'Postes de fabrication de ce modèle ({len(active_roles)} rôles actifs) :').classes('text-2xs font-bold text-slate-700 uppercase tracking-wide')
                    status_badge = ui.label('✅ Total : 100%' if is_valid else f'⚠️ Total : {current_sum:.0f}%').classes(
                        'text-xs font-bold font-mono px-2 py-0.5 rounded ' + 
                        ('bg-emerald-100 text-emerald-800' if is_valid else 'bg-amber-100 text-amber-800')
                    )
                    fields["status_badge"] = status_badge

                if available_roles_to_add:
                    with ui.row().classes('items-center gap-1.5'):
                        add_role_select = ui.select(
                            options={r["id"]: f'{r["label"]}' for r in available_roles_to_add},
                            value=available_roles_to_add[0]["id"]
                        ).props('outlined dense').classes('w-44 text-xs bg-white')

                        def do_add_role_to_model(t_id=item_id, sel=add_role_select):
                            target_rid = sel.value
                            r_obj = next((r for r in all_roles if r["id"] == target_rid), None)
                            def_pct = r_obj.get("default_pct", 10.0) if r_obj else 10.0
                            settings_mgr.add_role_to_type(t_id, target_rid, def_pct)
                            ui.notify(f'Rôle ajouté au modèle "{item["label"]}" !', type='positive')
                            render_accordion_list.refresh()

                        ui.button('➕ Ajouter ce rôle', on_click=do_add_role_to_model).props('outline color=primary size=sm').classes('text-xs font-bold')

            # Ligne 3 : Grille des rôles actifs pour ce modèle
            with ui.grid().classes(f'w-full grid-cols-1 sm:grid-cols-2 md:grid-cols-{min(max(len(active_roles), 1), 5)} gap-2.5'):
                for role in active_roles:
                    rid = role["id"]
                    pct_val = float(ratios.get(rid, role.get("default_pct", 10.0)))
                    allocated_min = round((total_time * pct_val) / 100.0, 1)

                    with ui.card().classes('bg-white border border-slate-200 rounded-lg p-2.5 shadow-2xs items-center text-center gap-1 relative'):
                        def make_remove_fn(t_id=item_id, r_id=rid, r_name=role["label"]):
                            def remove_fn():
                                if len(active_roles) <= 1:
                                    ui.notify('Un modèle doit comporter au moins un poste de production.', type='warning')
                                    return
                                settings_mgr.remove_role_from_type(t_id, r_id)
                                ui.notify(f'Poste "{r_name}" retiré de ce modèle.', type='info')
                                render_accordion_list.refresh()
                            return remove_fn

                        with ui.row().classes('w-full items-center justify-between'):
                            with ui.row().classes('items-center gap-1'):
                                ui.html(f'<div style="width: 7px; height: 7px; border-radius: 50%; background-color: {role["color"]};"></div>')
                                ui.label(role["label"]).classes('text-2xs font-bold text-slate-700 truncate max-w-[105px]')
                            
                            ui.button(on_click=make_remove_fn()).props('flat dense round size=xs icon=close color=negative').classes('text-2xs').tooltip('Retirer ce rôle de ce modèle')

                        pct_in = ui.number(
                            value=pct_val, 
                            min=0, 
                            max=100, 
                            step=1,
                            format='%d'
                        ).props('outlined dense suffix="%"').classes('w-20 text-center font-mono font-bold')
                        fields["pct_inputs"][rid] = pct_in

                        min_lbl = ui.label(f'{allocated_min} min').classes('text-2xs font-bold font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded')
                        fields["min_labels"][rid] = min_lbl

            def make_recalc_handler(f_dict, cur_active=active_roles):
                def recalc():
                    try:
                        curr_time = float(f_dict["time_input"].value or 0)
                        sum_pct = 0.0
                        for r_role in cur_active:
                            r_id = r_role["id"]
                            p_val = float(f_dict["pct_inputs"][r_id].value or 0)
                            sum_pct += p_val
                            mins = round((curr_time * p_val) / 100.0, 1)
                            f_dict["min_labels"][r_id].text = f'{mins} min'

                        if abs(sum_pct - 100.0) < 0.1:
                            f_dict["status_badge"].text = '✅ Total : 100%'
                            f_dict["status_badge"].classes(replace='text-xs font-bold font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800')
                        else:
                            diff = sum_pct - 100.0
                            sign = '+' if diff > 0 else ''
                            f_dict["status_badge"].text = f'⚠️ Total : {sum_pct:.0f}% (écart {sign}{diff:.0f}%)'
                            f_dict["status_badge"].classes(replace='text-xs font-bold font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-800')
                    except Exception as ex:
                        print("Erreur calcul réactif:", ex)
                return recalc

            recalc_fn = make_recalc_handler(fields)
            time_input.on('update:model-value', recalc_fn)
            for p_input in fields["pct_inputs"].values():
                p_input.on('update:model-value', recalc_fn)

            with ui.row().classes('w-full items-center justify-between pt-2 border-t border-slate-200'):
                ui.button(
                    '🗑️ Supprimer ce modèle', 
                    on_click=lambda tid=item_id, tlbl=item['label']: confirm_delete(tid, tlbl)
                ).props('flat color=negative size=sm').classes('font-bold text-xs')

                def save_action(tid=item_id, f_data=fields, cur_active=active_roles):
                    try:
                        new_time = float(f_data["time_input"].value)
                        new_ratios = {r["id"]: float(f_data["pct_inputs"][r["id"]].value) for r in cur_active}
                        settings_mgr.update_type(tid, {
                            "temps_moyen_min": new_time,
                            "ratios": new_ratios
                        })
                        ui.notify(f'Modèle "{item["label"]}" enregistré !', type='positive', position='bottom-right')
                        render_accordion_list.refresh()
                    except Exception as err:
                        ui.notify(f'Erreur : {err}', type='negative')

                ui.button('💾 Enregistrer ce modèle', on_click=save_action).props('color=primary size=sm').classes('font-bold shadow-xs px-4')


# =========================================================================
# SOUS-ONGLET 2 : ORGANISATION D'ATELIER (TABLES MULTI-RÔLES AVEC EMPLOYÉS)
# =========================================================================

@ui.refreshable
def render_workshop_tab():
    """Rendu complet du sous-onglet Organisation d'Atelier"""
    tables = settings_mgr.get_tables()
    roles = settings_mgr.get_roles()
    employees = settings_mgr.get_employees()

    # 1. Barre d'outils et réglage du nombre de tables
    with ui.card().classes('w-full bg-white border border-slate-200 rounded-xl p-4 shadow-2xs mb-5'):
        with ui.row().classes('w-full items-center justify-between flex-wrap gap-4'):
            with ui.column().classes('gap-0'):
                ui.label('Configuration des Tables de Travail').classes('text-base font-extrabold text-slate-900')
                ui.label('Chaque table peut assurer plusieurs rôles. Chaque rôle sur une table est affecté à un employé précis.').classes('text-xs text-slate-500')
            
            with ui.row().classes('items-center gap-3'):
                ui.label('Nombre de Tables :').classes('text-xs font-bold text-slate-700')
                
                def decrease_tables():
                    if len(tables) > 1:
                        settings_mgr.set_table_count(len(tables) - 1)
                        ui.notify(f'Nombre de tables ajusté à {len(tables) - 1}', type='info')
                        render_workshop_tab.refresh()
                ui.button('-', on_click=decrease_tables).props('outline dense size=sm').classes('w-8 font-bold')

                ui.label(f'{len(tables)}').classes('text-base font-mono font-extrabold px-3 py-1 bg-slate-100 rounded-lg border border-slate-300 text-slate-900')

                def increase_tables():
                    if len(tables) < 24:
                        settings_mgr.set_table_count(len(tables) + 1)
                        ui.notify(f'Nouvelle table ajoutée ! Total : {len(tables) + 1}', type='positive')
                        render_workshop_tab.refresh()
                ui.button('+', on_click=increase_tables).props('outline dense size=sm').classes('w-8 font-bold')

                ui.button('➕ Ajouter Table Personnalisée', on_click=open_add_table_dialog).props('color=primary size=sm').classes('font-bold shadow-xs text-xs ml-2')

    # 2. Section Rôles Atelier
    with ui.row().classes('w-full items-center justify-between mb-2 flex-wrap gap-2'):
        with ui.column().classes('gap-0'):
            ui.label('1. Postes & Rôles de Production de l\'Atelier').classes('text-sm font-extrabold text-slate-800')
            ui.label('Rôles disponibles pour le flux de fabrication et l\'affectation aux tables.').classes('text-2xs text-slate-500')
        
        ui.button('➕ Créer un Nouveau Rôle', on_click=open_add_role_dialog).props('color=secondary size=sm').classes('font-bold shadow-xs text-xs')

    with ui.grid().classes(f'w-full grid-cols-1 sm:grid-cols-2 md:grid-cols-{min(len(roles), 5)} gap-3 mb-6'):
        for r in roles:
            # Tables ayant ce rôle dans leurs assignments
            assigned_tables = [tb for tb in tables if any(a.get("role_id") == r["id"] for a in tb.get("role_assignments", []))]
            with ui.card().classes('bg-white border border-slate-200 rounded-xl p-3 shadow-2xs gap-1.5'):
                with ui.row().classes('items-center justify-between w-full'):
                    with ui.row().classes('items-center gap-1.5'):
                        ui.html(f'<div style="width: 10px; height: 10px; border-radius: 50%; background-color: {r["color"]};"></div>')
                        ui.label(r["label"]).classes('text-xs font-bold text-slate-900 truncate max-w-[120px]')
                    
                    with ui.row().classes('items-center gap-1'):
                        ui.button(on_click=lambda r_id=r["id"]: open_edit_role_dialog(r_id)).props('flat dense round size=xs icon=edit color=grey').classes('text-2xs')
                        if len(roles) > 1:
                            ui.button(on_click=lambda r_id=r["id"], r_lbl=r["label"]: confirm_delete_role(r_id, r_lbl)).props('flat dense round size=xs icon=delete color=negative').classes('text-2xs')

                ui.label(f'Poids moyen théorique : {r.get("default_pct", 10)}%').classes('text-2xs text-slate-400')

                if assigned_tables:
                    with ui.row().classes('items-center gap-1 mt-1 flex-wrap'):
                        for atb in assigned_tables:
                            ui.label(atb.get("code") or atb["name"]).classes('text-2xs font-mono font-bold text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded')
                else:
                    ui.label('⚠️ Aucune table assignée').classes('text-2xs text-amber-600 font-semibold mt-1')

    # 3. Grille des Tables de Travail (Multi-Rôles avec Employés)
    ui.label('2. Affectation Multi-Rôles & Opérateurs par Table de Travail').classes('text-sm font-extrabold text-slate-800 mb-2')
    with ui.grid().classes('w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'):
        for tb in tables:
            render_table_card(tb, roles, employees)

def render_table_card(tb: Dict[str, Any], roles: List[Dict[str, Any]], employees: List[Dict[str, Any]]):
    """Rendu d'une carte de table de travail supportant plusieurs rôles avec employés dédiés"""
    tb_id = tb["id"]
    assignments = tb.get("role_assignments", [])
    
    # Options employés
    emp_options = {e["id"]: f'{e["name"]} ({e["code"]})' for e in employees if e.get("active", True)}
    if not emp_options and employees:
        emp_options = {e["id"]: e["name"] for e in employees}

    # Rôles déjà présents sur cette table
    current_role_ids = {a["role_id"] for a in assignments}
    available_roles_to_assign = [r for r in roles if r["id"] not in current_role_ids]

    with ui.card().classes('bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:shadow-xs transition-all gap-3'):
        # En-tête de la table
        with ui.row().classes('w-full items-center justify-between border-b border-slate-100 pb-2'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('table_restaurant', size='sm').classes('text-blue-600')
                with ui.column().classes('gap-0'):
                    ui.label(tb["name"]).classes('text-sm font-bold text-slate-900')
                    ui.label(f'Identifiant : {tb.get("code", tb_id)}').classes('text-2xs text-slate-400 font-mono')
            
            ui.label(f'{len(assignments)} rôle(s)').classes('text-2xs font-bold px-2 py-0.5 rounded font-mono bg-blue-50 text-blue-700 border border-blue-200')

        # Liste des rôles configurés sur cette table avec leurs employés assignés
        with ui.column().classes('w-full gap-2'):
            ui.label('Rôles assurés & Opérateurs dédiés :').classes('text-2xs font-bold text-slate-600 uppercase tracking-wide')
            
            if not assignments:
                ui.label('Aucun rôle affecté pour l\'instant.').classes('text-2xs text-slate-400 italic')

            for a in assignments:
                rid = a.get("role_id")
                eid = a.get("employee_id")
                role_obj = next((r for r in roles if r["id"] == rid), None)
                if not role_obj:
                    continue

                with ui.card().classes('w-full bg-slate-50 border border-slate-200 rounded-lg p-2 gap-1.5 shadow-2xs'):
                    with ui.row().classes('w-full items-center justify-between'):
                        with ui.row().classes('items-center gap-1.5'):
                            ui.html(f'<div style="width: 8px; height: 8px; border-radius: 50%; background-color: {role_obj["color"]};"></div>')
                            ui.label(role_obj["label"]).classes('text-2xs font-bold text-slate-800')
                        
                        # Bouton retirer ce rôle de la table
                        def make_del_assign(t_id=tb_id, target_rid=rid):
                            def del_fn():
                                settings_mgr.remove_role_from_table(t_id, target_rid)
                                ui.notify(f'Rôle retiré de {tb["name"]}.', type='info')
                                render_workshop_tab.refresh()
                                render_employees_tab.refresh()
                            return del_fn

                        ui.button(on_click=make_del_assign()).props('flat dense round size=xs icon=close color=negative').classes('text-2xs').tooltip('Retirer ce rôle de la table')

                    # Sélecteur de l'employé assigné à ce rôle précis
                    with ui.row().classes('w-full items-center gap-1'):
                        ui.icon('person', size='xs').classes('text-slate-400')
                        
                        def make_emp_change(t_id=tb_id, target_rid=rid):
                            def on_change(e):
                                settings_mgr.update_table_role_employee(t_id, target_rid, e.value)
                                ui.notify(f'Opérateur mis à jour sur {tb["name"]} !', type='positive', position='bottom-right')
                                render_workshop_tab.refresh()
                                render_employees_tab.refresh()
                            return on_change

                        ui.select(
                            options=emp_options, 
                            value=eid if eid in emp_options else (list(emp_options.keys())[0] if emp_options else ""),
                            on_change=make_emp_change(tb_id, rid)
                        ).props('outlined dense').classes('w-full text-2xs bg-white')

        # Formulaire d'ajout d'un nouveau rôle sur la table
        if available_roles_to_assign and employees:
            with ui.row().classes('w-full items-center justify-between pt-1 flex-wrap gap-1 border-t border-dashed border-slate-200 mt-1'):
                with ui.row().classes('items-center gap-1 flex-1'):
                    add_role_sel = ui.select(
                        options={r["id"]: r["label"] for r in available_roles_to_assign},
                        value=available_roles_to_assign[0]["id"]
                    ).props('outlined dense').classes('w-28 text-2xs bg-white')

                    add_emp_sel = ui.select(
                        options=emp_options,
                        value=list(emp_options.keys())[0] if emp_options else ""
                    ).props('outlined dense').classes('flex-1 text-2xs bg-white')

                def make_add_assign(t_id=tb_id, r_sel=add_role_sel, e_sel=add_emp_sel):
                    def add_fn():
                        settings_mgr.add_role_to_table(t_id, r_sel.value, e_sel.value)
                        ui.notify(f'Rôle assigné à {tb["name"]} !', type='positive')
                        render_workshop_tab.refresh()
                        render_employees_tab.refresh()
                    return add_fn

                ui.button('➕ Assigner', on_click=make_add_assign()).props('outline color=primary size=xs').classes('font-bold text-2xs')

        # Équipement / Machine
        with ui.column().classes('w-full gap-1'):
            ui.label('Équipement / Machine associée :').classes('text-2xs font-bold text-slate-600 uppercase tracking-wide')
            desc_input = ui.input(
                value=tb.get("description", "")
            ).props('outlined dense placeholder="Ex: Tronçonneuse, Sertisseuse..."').classes('w-full text-xs bg-white')

        with ui.row().classes('w-full items-center justify-between pt-2 border-t border-slate-100'):
            def delete_table_action(t_id=tb_id, t_name=tb["name"]):
                settings_mgr.delete_table(t_id)
                ui.notify(f'"{t_name}" supprimée.', type='info')
                render_workshop_tab.refresh()
                render_employees_tab.refresh()

            ui.button('🗑️ Retirer', on_click=delete_table_action).props('flat color=negative size=sm').classes('text-xs font-bold')

            def save_table_details(t_id=tb_id, desc_in=desc_input):
                settings_mgr.update_table(t_id, {
                    "description": desc_in.value.strip()
                })
                ui.notify(f'Table "{tb["name"]}" enregistrée !', type='positive')
                render_workshop_tab.refresh()

            ui.button('💾 Enregistrer', on_click=save_table_details).props('color=primary size=sm').classes('text-xs font-bold shadow-xs px-3')


# =========================================================================
# SOUS-ONGLET 3 : EMPLOYÉS D'ATELIER (REGISTRE DES OPÉRATEURS & TECHNICIENS)
# =========================================================================

@ui.refreshable
# =========================================================================
# SOUS-ONGLET 3 : EMPLOYÉS D'ATELIER (POINTAGE EN TEMPS RÉEL & FACE ID)
# =========================================================================

@ui.refreshable
def render_employees_tab():
    """Rendu complet du sous-onglet Employés d'Atelier avec Pointage & Face ID"""
    employees = settings_mgr.get_employees()
    tables = settings_mgr.get_tables()
    roles = settings_mgr.get_roles()

    # Compteurs de présence
    present_count = len([e for e in employees if e.get("presence_status") == "PRESENT"])
    break_count = len([e for e in employees if e.get("presence_status") == "BREAK"])
    absent_count = len([e for e in employees if e.get("presence_status") in ("ABSENT", "LEFT") or not e.get("active", True)])

    # 1. En-tête et statistiques d'équipe & pointage
    with ui.card().classes('w-full bg-white border border-slate-200 rounded-xl p-5 shadow-2xs mb-5'):
        with ui.row().classes('w-full items-center justify-between flex-wrap gap-4'):
            with ui.column().classes('gap-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.label('Gestion des Employés & Pointage Atelier').classes('text-lg font-extrabold text-slate-900')
                    ui.label('Face ID & Biométrie').classes('text-2xs font-bold bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full')
                ui.label('Suivi de présence en temps réel, reconnaissance faciale Face ID et affectation aux postes de travail.').classes('text-xs text-slate-500')
            
            with ui.row().classes('items-center gap-2 flex-wrap'):
                # Badges de présence en temps réel
                with ui.row().classes('items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-mono font-bold'):
                    ui.label(f'👥 {len(employees)} Total').classes('text-slate-700')
                    ui.label('•').classes('text-slate-300')
                    ui.label(f'🟢 {present_count} Présents').classes('text-emerald-700')
                    if break_count > 0:
                        ui.label('•').classes('text-slate-300')
                        ui.label(f'🟠 {break_count} Pause').classes('text-amber-700')
                    ui.label('•').classes('text-slate-300')
                    ui.label(f'⚪ {absent_count} Non pointés').classes('text-slate-400')

                # Bouton QR Code Borne Pointage
                ui.button('📱 Borne Pointage & QR Code', on_click=open_qr_kiosk_dialog).props('outline color=primary size=sm').classes('font-bold shadow-2xs text-xs')
                # Bouton Nouvel Employé
                ui.button('➕ Nouvel Employé', on_click=open_add_employee_dialog).props('color=primary size=sm').classes('font-bold shadow-xs text-xs')

    # 2. Grille des cartes employés
    with ui.grid().classes('w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6'):
        for emp in employees:
            render_employee_card(emp, tables, roles)

    # 3. Journal des derniers pointages Face ID
    render_recent_punches_section()

def render_employee_card(emp: Dict[str, Any], tables: List[Dict[str, Any]], roles: List[Dict[str, Any]]):
    """Rendu de la carte détaillée d'un employé avec statut de pointage, Face ID et rôles"""
    emp_id = emp["id"]
    presence_status = emp.get("presence_status", "ABSENT")
    last_punch = emp.get("last_punch_at")
    has_face_id = emp.get("face_id_enrolled", False)
    
    # Recherche des tables et rôles où cet employé est assigné
    assigned_work: List[Dict[str, Any]] = []
    for tb in tables:
        for a in tb.get("role_assignments", []):
            if a.get("employee_id") == emp_id:
                r_obj = next((r for r in roles if r["id"] == a.get("role_id")), None)
                assigned_work.append({
                    "table_name": tb["name"],
                    "table_code": tb.get("code", tb["name"]),
                    "role_label": r_obj["label"] if r_obj else a.get("role_id"),
                    "role_color": r_obj["color"] if r_obj else "#64748B"
                })

    # Initiales pour l'avatar
    name_parts = emp["name"].strip().split()
    initials = (name_parts[0][0] + (name_parts[1][0] if len(name_parts) > 1 else "")).upper() if name_parts else "OP"

    with ui.card().classes('bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:shadow-xs transition-all gap-3'):
        # En-tête employé avec statut de pointage
        with ui.row().classes('w-full items-center justify-between border-b border-slate-100 pb-2.5'):
            with ui.row().classes('items-center gap-3'):
                ui.avatar(initials, color='blue-1', text_color='blue-8', size='md').classes('font-bold font-mono')
                with ui.column().classes('gap-0'):
                    ui.label(emp["name"]).classes('text-sm font-extrabold text-slate-900')
                    ui.label(f'Matricule : {emp.get("code", emp_id)}').classes('text-2xs text-slate-400 font-mono')
            
            # Badge de Statut de Pointage
            if presence_status == "PRESENT":
                with ui.row().classes('items-center gap-1 bg-emerald-50 border border-emerald-200 text-emerald-800 px-2 py-0.5 rounded text-2xs font-bold font-mono'):
                    ui.html('<div style="width: 7px; height: 7px; border-radius: 50%; background-color: #10B981; animation: pulse 2s infinite;"></div>')
                    ui.label(f'Pointé ({last_punch or "Présent"})')
            elif presence_status == "BREAK":
                with ui.row().classes('items-center gap-1 bg-amber-50 border border-amber-200 text-amber-800 px-2 py-0.5 rounded text-2xs font-bold font-mono'):
                    ui.label(f'🟠 Pause ({last_punch})')
            else:
                with ui.row().classes('items-center gap-1 bg-slate-100 border border-slate-200 text-slate-500 px-2 py-0.5 rounded text-2xs font-bold font-mono'):
                    ui.label('⚪ Non pointé')

        # Statut Biométrique Face ID & Spécialité
        with ui.column().classes('gap-1'):
            with ui.row().classes('items-center justify-between'):
                with ui.row().classes('items-center gap-1.5'):
                    ui.icon('badge', size='xs').classes('text-slate-400')
                    ui.label(emp.get("specialty") or "Opérateur atelier").classes('text-xs font-semibold text-slate-700')
                
                # Badge Face ID
                if has_face_id:
                    with ui.row().classes('items-center gap-1 bg-blue-50 border border-blue-200 text-blue-700 px-1.5 py-0.5 rounded text-3xs font-bold'):
                        ui.icon('face', size='xs')
                        ui.label('Face ID Actif')
                else:
                    with ui.row().classes('items-center gap-1 bg-rose-50 border border-rose-200 text-rose-600 px-1.5 py-0.5 rounded text-3xs font-bold'):
                        ui.icon('no_photography', size='xs')
                        ui.label('Sans Face ID')

            if emp.get("phone"):
                with ui.row().classes('items-center gap-1.5'):
                    ui.icon('call', size='xs').classes('text-slate-400')
                    ui.label(emp["phone"]).classes('text-xs text-slate-500 font-mono')

        # Affectations actuelles sur les tables
        with ui.column().classes('w-full gap-1 pt-1 border-t border-slate-100'):
            ui.label(f'Postes assignés ({len(assigned_work)}) :').classes('text-2xs font-bold text-slate-500 uppercase tracking-wide')
            if assigned_work:
                with ui.row().classes('items-center gap-1.5 flex-wrap'):
                    for w in assigned_work:
                        with ui.row().classes('items-center gap-1 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded text-2xs'):
                            ui.html(f'<div style="width: 6px; height: 6px; border-radius: 50%; background-color: {w["role_color"]};"></div>')
                            ui.label(f'{w["table_code"]} : {w["role_label"]}').classes('font-semibold text-slate-700')
            else:
                ui.label('Non affecté actuellement à une table').classes('text-2xs text-slate-400 italic')

        # Boutons d'actions (Pointer, Face ID, Modifier, Supprimer)
        with ui.row().classes('w-full items-center justify-between gap-1 pt-2 border-t border-slate-100 flex-wrap'):
            # Action Pointer / Dépointer en un clic
            def make_toggle_punch(e_id=emp_id, cur_st=presence_status, e_name=emp["name"]):
                def do_punch():
                    res = settings_mgr.record_punch(e_id, punch_type="AUTO", method="MANUAL_ADMIN")
                    act = "Entrée" if res["punch_type"] == "IN" else "Sortie"
                    ui.notify(f'Pointage {act} enregistré pour {e_name} ({res["time_short"]}) !', type='positive', position='bottom-right')
                    render_employees_tab.refresh()
                return do_punch

            if presence_status == "PRESENT":
                ui.button('🚪 Pointer Sortie', on_click=make_toggle_punch()).props('outline color=negative size=xs').classes('font-bold text-2xs')
            else:
                ui.button('⏱️ Pointer Entrée', on_click=make_toggle_punch()).props('outline color=positive size=xs').classes('font-bold text-2xs')

            with ui.row().classes('items-center gap-1'):
                # Bouton Enrôler / Mettre à jour Face ID
                ui.button(on_click=lambda e_id=emp_id: open_face_enroll_dialog(e_id)).props('flat dense round size=sm icon=face color=primary').tooltip('Enregistrer / Modifier le Face ID')
                # Bouton Modifier
                ui.button(on_click=lambda e_id=emp_id: open_edit_employee_dialog(e_id)).props('flat dense round size=sm icon=edit color=grey').tooltip('Modifier')
                # Bouton Supprimer
                if len(settings_mgr.get_employees()) > 1:
                    ui.button(on_click=lambda e_id=emp_id, e_name=emp["name"]: confirm_delete_employee(e_id, e_name)).props('flat dense round size=sm icon=delete color=negative').tooltip('Supprimer')

def render_recent_punches_section():
    """Affichage du journal récent des pointages de l'atelier"""
    punches = settings_mgr.get_recent_punches(limit=10)
    with ui.card().classes('w-full bg-white border border-slate-200 rounded-xl p-4 shadow-2xs'):
        with ui.row().classes('w-full items-center justify-between mb-3'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('history', size='sm').classes('text-blue-600')
                ui.label('Journal Récent des Pointages (Face ID & Borne)').classes('text-sm font-bold text-slate-800')
            ui.label(f'{len(punches)} derniers pointages').classes('text-2xs font-mono text-slate-400')

        if punches:
            with ui.column().classes('w-full gap-1.5'):
                for p in punches:
                    with ui.row().classes('w-full items-center justify-between bg-slate-50 border border-slate-100 rounded-lg p-2 px-3 text-xs'):
                        with ui.row().classes('items-center gap-2.5'):
                            if p["punch_type"] == "IN":
                                ui.label('🟢 ENTRÉE').classes('text-2xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded font-mono')
                            elif p["punch_type"] == "OUT":
                                ui.label('🔴 SORTIE').classes('text-2xs font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded font-mono')
                            elif p["punch_type"] == "BREAK_START":
                                ui.label('🟠 PAUSE').classes('text-2xs font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded font-mono')
                            else:
                                ui.label(f'🔵 {p["punch_type"]}').classes('text-2xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded font-mono')
                            
                            ui.label(p.get("employee_name", "Employé")).classes('font-bold text-slate-800')
                            ui.label(f'({p.get("employee_code", "")})').classes('text-slate-400 font-mono text-2xs')

                        with ui.row().classes('items-center gap-3 text-2xs text-slate-500 font-mono'):
                            method_badge = '📷 Face ID' if p.get("method") == "FACE_ID" else '👤 Manuel'
                            ui.label(method_badge).classes('bg-white border border-slate-200 px-1.5 py-0.5 rounded')
                            if p.get("confidence"):
                                ui.label(f'Confiance: {int(p["confidence"] * 100)}%').classes('text-slate-400')
                            ui.label(p.get("punch_time", "")).classes('text-slate-600 font-bold')
        else:
            with ui.row().classes('w-full items-center justify-center p-6 text-slate-400 text-xs italic'):
                ui.label('Aucun pointage enregistré pour le moment. Les pointages apparaîtront ici en direct.')

# --- Dialogues Employés & Borne QR Code ---

def get_local_ip() -> str:
    """Détecte l'adresse IP locale du PC sur le réseau Wi-Fi / Ethernet"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def open_qr_kiosk_dialog():
    """Dialogue affichant le QR Code officiel de la borne de pointage Face ID pour mobile et tablette"""
    local_ip = get_local_ip()
    default_url = f"http://{local_ip}:8000/pointage"
    qr_state = {"url": default_url}

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-2xl w-[460px] max-w-full text-center items-center gap-3 shadow-2xl'):
        ui.icon('qr_code_scanner', size='md').classes('text-blue-600')
        ui.label('Borne de Pointage Face ID (Mobile / Tablette)').classes('text-lg font-extrabold text-slate-900')
        ui.label('Flashez ce QR Code avec votre smartphone ou tablette connectée au Wi-Fi de l\'atelier.').classes('text-xs text-slate-500 px-2 leading-relaxed')

        # Affichage du QR Code généré
        with ui.card().classes('p-3 bg-white border border-slate-200 rounded-xl shadow-2xs my-1'):
            qr_img = ui.image(settings_mgr.generate_kiosk_qr(default_url)).classes('w-56 h-56 rounded-lg')

        # Champ d'URL modifiable pour basculer facilement (ex: Tunnel HTTPS ou IP Wi-Fi)
        with ui.column().classes('w-full gap-2 text-left'):
            ui.label('URL ciblée par le QR Code :').classes('text-3xs font-bold uppercase tracking-wider text-slate-500')
            url_input = ui.input(value=default_url).props('outlined dense').classes('w-full font-mono text-xs')
            
            def update_qr():
                target = (url_input.value or '').strip() or default_url
                qr_state["url"] = target
                qr_img.set_source(settings_mgr.generate_kiosk_qr(target))
                ui.notify('QR Code mis à jour avec la nouvelle URL !', type='info')
            
            url_input.on('change', update_qr)

            # Raccourcis rapides
            with ui.row().classes('w-full items-center justify-between text-2xs'):
                def set_wifi():
                    url_input.set_value(f"http://{local_ip}:8000/pointage")
                    update_qr()
                def set_local():
                    url_input.set_value("http://localhost:8000/pointage")
                    update_qr()

                ui.button(f'📶 Wi-Fi Atelier ({local_ip})', on_click=set_wifi).props('outline size=xs color=primary').classes('font-bold')
                ui.button('💻 Localhost (Ce PC)', on_click=set_local).props('flat size=xs color=grey').classes('font-bold')

        # Note de sécurité sur la caméra mobile (HTTPS vs HTTP)
        with ui.column().classes('w-full gap-1.5 bg-blue-50/70 border border-blue-200 p-3 rounded-xl text-left text-2xs text-blue-950'):
            with ui.row().classes('items-center gap-1.5'):
                ui.icon('info', size='xs').classes('text-blue-600')
                ui.label('Comment ouvrir sur smartphone avec la Caméra :').classes('font-bold text-xs')
            ui.label('1. Sur le même Wi-Fi : Ouvrez l\'adresse ci-dessus dans votre navigateur mobile.').classes('text-slate-600')
            ui.label('2. Caméra sur mobile : Les navigateurs (iPhone/Android) exigent une connexion HTTPS pour activer la caméra. Lancez le fichier "start_tunnel.bat" sur votre PC pour obtenir un lien HTTPS direct !').classes('text-blue-900 font-semibold')
            ui.label('3. Code PIN Admin Borne : 1234 (pour créer un employé sur place)').classes('font-mono font-bold text-slate-700 pt-1')

        with ui.row().classes('w-full justify-center gap-2 pt-1'):
            ui.button('Fermer', on_click=dialog.close).props('flat color=grey')
            ui.button('🌐 Ouvrir la Borne sur ce PC', on_click=lambda: ui.navigate.to('/pointage', new_tab=True)).props('color=primary').classes('font-bold shadow-xs text-xs')
    dialog.open()

def open_face_enroll_dialog(emp_id: str):
    """Dialogue avec caméra interactive pour enrôler ou mettre à jour le visage Face ID d'un employé"""
    emp = next((e for e in settings_mgr.get_employees() if e["id"] == emp_id), None)
    if not emp:
        return

    captured_photo = {"data": None}

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-2xl w-[440px] max-w-full text-center items-center gap-3 shadow-xl'):
        ui.icon('face', size='md').classes('text-blue-600')
        ui.label(f'Enrôlement Face ID : {emp["name"]}').classes('text-base font-extrabold text-slate-900')
        ui.label('Positionnez votre visage devant la caméra et cliquez sur "Prendre Photo Face ID".').classes('text-xs text-slate-500 leading-relaxed')

        # Zone d'affichage Caméra / Photo capturée
        with ui.element('div').classes('w-full relative rounded-xl overflow-hidden bg-slate-950 flex flex-col items-center justify-center').style('height: 240px;'):
            # Conteneur vidéo
            ui.html('<video id="enroll-cam" autoplay playsinline muted style="width: 100%; height: 240px; object-fit: cover;"></video>')
            # Mire ovale
            ui.html('''
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 140px; height: 180px; border: 2px dashed #3B82F6; border-radius: 50%; pointer-events: none; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);"></div>
            ''')
            # Image de prévisualisation si photo prise
            preview_img = ui.image('').classes('absolute inset-0 w-full h-full object-cover hidden rounded-xl')

        # Barre d'état caméra
        ui.html('<div id="enroll-cam-status" class="text-2xs font-mono text-slate-500 font-semibold">● Caméra prête</div>')

        # Boutons de contrôle caméra
        with ui.row().classes('w-full items-center justify-center gap-2'):
            async def start_enroll_cam():
                await ui.run_javascript("window.suiviCam.start('enroll-cam', 'enroll-cam-status')")
                preview_img.classes(add='hidden')

            async def capture_enroll_photo():
                photo_b64 = await ui.run_javascript("window.suiviCam.capture('enroll-cam')")
                if photo_b64 and len(str(photo_b64)) > 100:
                    captured_photo["data"] = photo_b64
                    preview_img.set_source(photo_b64)
                    preview_img.classes(remove='hidden')
                    ui.notify('Visage capturé avec succès !', type='positive')
                else:
                    ui.notify('Veuillez d\'abord allumer la caméra.', type='warning')

            ui.button('📷 Allumer Caméra', on_click=start_enroll_cam).props('outline size=sm color=primary').classes('font-bold text-xs')
            ui.button('📸 Prendre Photo Face ID', on_click=capture_enroll_photo).props('color=primary size=sm').classes('font-bold text-xs shadow-xs')

        # Option import de fichier photo alternatif
        def handle_upload(e):
            import base64
            b64_content = base64.b64encode(e.content.read()).decode('utf-8')
            mime = e.type or 'image/jpeg'
            data_url = f"data:{mime};base64,{b64_content}"
            captured_photo["data"] = data_url
            preview_img.set_source(data_url)
            preview_img.classes(remove='hidden')
            ui.notify(f'Photo importée avec succès !', type='positive')

        with ui.expansion('Ou importer une photo depuis l\'ordinateur...', icon='folder').classes('w-full text-2xs text-slate-500 border border-slate-200 rounded-lg'):
            ui.upload(on_upload=handle_upload, max_files=1).props('dense outlined accept="image/*"').classes('w-full text-2xs')

        with ui.row().classes('w-full justify-end gap-2 pt-2 border-t border-slate-100'):
            def on_close():
                ui.run_javascript("window.suiviCam.stop('enroll-cam')")
                dialog.close()

            ui.button('Annuler', on_click=on_close).props('flat color=grey')

            def do_save_face():
                photo = captured_photo["data"] or "data:image/png;base64,default_enrolled_face"
                settings_mgr.save_face_credential(emp_id, photo_data_url=photo)
                on_close()
                ui.notify(f'Face ID de {emp["name"]} enregistré et activé !', type='positive')
                render_employees_tab.refresh()

            ui.button('💾 Enregistrer Face ID', on_click=do_save_face).props('color=positive').classes('font-bold shadow-xs')

    dialog.open()
    ui.timer(0.2, lambda: ui.run_javascript("window.suiviCam.start('enroll-cam', 'enroll-cam-status')"), once=True)


def open_add_employee_dialog():
    """Dialogue pour ajouter un employé avec capture interactive de son Face ID"""
    current_count = len(settings_mgr.get_employees())
    next_num = current_count + 1
    new_captured_photo = {"data": None}

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-2xl w-[440px] max-w-full'):
        ui.label('➕ Nouvel Employé d\'Atelier').classes('text-base font-extrabold text-slate-900 mb-1')
        ui.label('Renseignez les coordonnées et capturez le Face ID de l\'opérateur.').classes('text-xs text-slate-500 mb-3')

        e_name = ui.input('Nom complet', placeholder='Ex: Karim Benali').props('outlined dense').classes('w-full mb-2')
        e_code = ui.input('Matricule / Code', value=f'EMP-{next_num:02d}').props('outlined dense').classes('w-full mb-2')
        e_spec = ui.input('Spécialité / Métier', placeholder='Ex: Débit, Assemblage, Vitrage...').props('outlined dense').classes('w-full mb-2')
        e_phone = ui.input('Téléphone / Contact', placeholder='Ex: 06 12 34 56 78').props('outlined dense').classes('w-full mb-3')

        # Section Caméra Face ID
        with ui.card().classes('w-full p-3 bg-slate-50 border border-slate-200 rounded-xl items-center gap-2 mb-3'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('items-center gap-1.5'):
                    ui.icon('face', size='xs').classes('text-blue-600')
                    ui.label('Enrôlement Face ID Caméra').classes('text-xs font-bold text-slate-800')
                ui.html('<div id="add-cam-status" class="text-3xs font-mono text-slate-500 font-semibold">● Prêt</div>')

            with ui.element('div').classes('w-full relative rounded-lg overflow-hidden bg-slate-950 flex flex-col items-center justify-center').style('height: 180px;'):
                ui.html('<video id="add-emp-cam" autoplay playsinline muted style="width: 100%; height: 180px; object-fit: cover;"></video>')
                ui.html('''
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 110px; height: 140px; border: 2px dashed #3B82F6; border-radius: 50%; pointer-events: none; box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);"></div>
                ''')
                add_preview_img = ui.image('').classes('absolute inset-0 w-full h-full object-cover hidden rounded-lg')

            with ui.row().classes('w-full items-center justify-center gap-2'):
                async def start_add_cam():
                    await ui.run_javascript("window.suiviCam.start('add-emp-cam', 'add-cam-status')")
                    add_preview_img.classes(add='hidden')

                async def capture_add_photo():
                    photo_b64 = await ui.run_javascript("window.suiviCam.capture('add-emp-cam')")
                    if photo_b64 and len(str(photo_b64)) > 100:
                        new_captured_photo["data"] = photo_b64
                        add_preview_img.set_source(photo_b64)
                        add_preview_img.classes(remove='hidden')
                        ui.notify('Visage capturé avec succès !', type='positive')
                    else:
                        started = await ui.run_javascript("window.suiviCam.start('add-emp-cam', 'add-cam-status')")
                        if not started:
                            ui.notify('Activez la caméra ou importez une photo ci-dessous.', type='warning')
                        else:
                            ui.notify('Caméra allumée ! Re-cliquez sur "Capturer le Visage".', type='info')

                ui.button('📷 Allumer Caméra', on_click=start_add_cam).props('outline size=xs color=primary').classes('font-bold text-2xs')
                ui.button('📸 Capturer le Visage', on_click=capture_add_photo).props('color=primary size=xs').classes('font-bold text-2xs shadow-xs')

        # Option import alternatif si la caméra est indisponible
        def handle_add_upload(e):
            import base64
            b64_content = base64.b64encode(e.content.read()).decode('utf-8')
            mime = e.type or 'image/jpeg'
            data_url = f"data:{mime};base64,{b64_content}"
            new_captured_photo["data"] = data_url
            add_preview_img.set_source(data_url)
            add_preview_img.classes(remove='hidden')
            ui.notify('Photo importée avec succès !', type='positive')

        with ui.expansion('Ou importer une photo depuis l\'ordinateur...', icon='folder').classes('w-full text-2xs text-slate-500 border border-slate-200 rounded-lg mb-3'):
            ui.upload(on_upload=handle_add_upload, max_files=1).props('dense outlined accept="image/*"').classes('w-full text-2xs')

        with ui.row().classes('w-full justify-end gap-2'):
            def on_add_close():
                ui.run_javascript("window.suiviCam.stop('add-emp-cam')")
                dialog.close()

            ui.button('Annuler', on_click=on_add_close).props('flat color=grey')

            def do_add_emp():
                if not e_name.value or not e_name.value.strip():
                    ui.notify('Veuillez renseigner un nom.', type='warning')
                    return
                has_face = bool(new_captured_photo["data"])
                settings_mgr.add_employee({
                    "name": e_name.value.strip(),
                    "code": e_code.value.strip() or f'EMP-{next_num:02d}',
                    "specialty": e_spec.value.strip() or 'Opérateur atelier',
                    "phone": e_phone.value.strip(),
                    "active": True,
                    "presence_status": "PRESENT",
                    "face_id_enrolled": True,
                    "face_photo": new_captured_photo["data"] or "data:image/png;base64,default_face"
                })
                on_add_close()
                ui.notify(f'Employé "{e_name.value}" créé avec Face ID actif !', type='positive')
                render_employees_tab.refresh()
                render_workshop_tab.refresh()

            ui.button('Enregistrer l\'Employé', on_click=do_add_emp).props('color=primary').classes('font-bold shadow-xs')

    dialog.open()
    ui.timer(0.2, lambda: ui.run_javascript("window.suiviCam.start('add-emp-cam', 'add-cam-status')"), once=True)


def open_edit_employee_dialog(emp_id: str):
    """Dialogue pour modifier un employé"""
    employees = settings_mgr.get_employees()
    emp_obj = next((e for e in employees if e["id"] == emp_id), None)
    if not emp_obj:
        return

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl w-96 max-w-full'):
        ui.label(f'✏️ Modifier l\'Employé "{emp_obj["name"]}"').classes('text-base font-bold text-slate-900 mb-1')
        ui.label('Mettez à jour les informations et l\'état de présence.').classes('text-xs text-slate-500 mb-4')

        e_name = ui.input('Nom complet', value=emp_obj["name"]).props('outlined dense').classes('w-full mb-2')
        e_code = ui.input('Matricule / Code', value=emp_obj.get("code", "")).props('outlined dense').classes('w-full mb-2')
        e_spec = ui.input('Spécialité / Métier', value=emp_obj.get("specialty", "")).props('outlined dense').classes('w-full mb-2')
        e_phone = ui.input('Téléphone / Contact', value=emp_obj.get("phone", "")).props('outlined dense').classes('w-full mb-3')
        
        status_opts = {
            "PRESENT": "🟢 Présent / Pointé",
            "BREAK": "🟠 En Pause",
            "ABSENT": "⚪ Absent / Non Pointé"
        }
        e_status = ui.select(options=status_opts, value=emp_obj.get("presence_status", "PRESENT"), label="Statut de présence").props('outlined dense').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_save_emp():
                if not e_name.value or not e_name.value.strip():
                    ui.notify('Veuillez renseigner un nom.', type='warning')
                    return
                settings_mgr.update_employee(emp_id, {
                    "name": e_name.value.strip(),
                    "code": e_code.value.strip(),
                    "specialty": e_spec.value.strip(),
                    "phone": e_phone.value.strip(),
                    "presence_status": e_status.value,
                    "active": e_status.value != "ABSENT"
                })
                dialog.close()
                ui.notify(f'Employé "{e_name.value}" mis à jour !', type='positive')
                render_employees_tab.refresh()
                render_workshop_tab.refresh()
            ui.button('Enregistrer', on_click=do_save_emp).props('color=primary')
    dialog.open()

def confirm_delete_employee(emp_id: str, emp_name: str):
    """Dialogue de confirmation de suppression d'un employé"""
    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl'):
        ui.label(f'Supprimer l\'employé "{emp_name}" ?').classes('text-base font-bold text-slate-900')
        ui.label('Ses affectations sur les tables d\'atelier seront automatiquement réassignées.').classes('text-xs text-slate-500 mb-4')
        with ui.row().classes('w-full justify-end gap-3'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_del():
                try:
                    settings_mgr.delete_employee(emp_id)
                    dialog.close()
                    ui.notify(f'Employé "{emp_name}" supprimé.', type='info')
                    render_employees_tab.refresh()
                    render_workshop_tab.refresh()
                except Exception as ex:
                    ui.notify(str(ex), type='negative')
            ui.button('Confirmer la suppression', on_click=do_del).props('color=negative')
    dialog.open()


# --- Dialogues de Gestion des Rôles et Tables ---

def open_add_role_dialog():
    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl w-96 max-w-full'):
        ui.label('➕ Nouveau Rôle Atelier').classes('text-base font-bold text-slate-900 mb-1')
        ui.label('Créez un rôle ou une étape de production sur-mesure.').classes('text-xs text-slate-500 mb-4')

        r_label = ui.input('Nom du rôle / poste', placeholder='Ex: Quincaillerie, Soudure...').props('outlined dense').classes('w-full mb-2')
        r_pct = ui.number('Poids théorique par défaut (%)', value=10, min=1, max=100, step=1).props('outlined dense suffix="%"').classes('w-full mb-2')
        
        ui.label('Couleur d\'identification :').classes('text-2xs font-bold text-slate-600 uppercase mb-1')
        r_color_select = ui.select(
            options={c: f'Couleur {c}' for c in ROLE_COLORS}, 
            value=ROLE_COLORS[5],
            label='Palette'
        ).props('outlined dense').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_add_role():
                if not r_label.value or not r_label.value.strip():
                    ui.notify('Veuillez renseigner un nom de rôle.', type='warning')
                    return
                settings_mgr.add_role({
                    "label": r_label.value.strip(),
                    "color": r_color_select.value,
                    "default_pct": float(r_pct.value or 10)
                })
                dialog.close()
                ui.notify(f'Rôle "{r_label.value}" créé avec succès !', type='positive')
                render_workshop_tab.refresh()
                render_roles_legend.refresh()
                render_accordion_list.refresh()
            ui.button('Créer ce Rôle', on_click=do_add_role).props('color=primary')
    dialog.open()

def open_edit_role_dialog(role_id: str):
    roles = settings_mgr.get_roles()
    role_obj = next((r for r in roles if r["id"] == role_id), None)
    if not role_obj:
        return

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl w-96 max-w-full'):
        ui.label(f'✏️ Modifier le Rôle "{role_obj["label"]}"').classes('text-base font-bold text-slate-900 mb-1')
        ui.label('Mettez à jour le nom, la couleur ou le poids par défaut.').classes('text-xs text-slate-500 mb-4')

        r_label = ui.input('Nom du rôle', value=role_obj["label"]).props('outlined dense').classes('w-full mb-2')
        r_pct = ui.number('Poids théorique par défaut (%)', value=role_obj.get("default_pct", 10), min=1, max=100, step=1).props('outlined dense suffix="%"').classes('w-full mb-2')
        
        ui.label('Couleur d\'identification :').classes('text-2xs font-bold text-slate-600 uppercase mb-1')
        current_color = role_obj.get("color", ROLE_COLORS[0])
        color_opts = {c: f'Couleur {c}' for c in ROLE_COLORS}
        if current_color not in color_opts:
            color_opts[current_color] = f'Personnalisée ({current_color})'
            
        r_color_select = ui.select(
            options=color_opts, 
            value=current_color,
            label='Palette'
        ).props('outlined dense').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_save_role():
                if not r_label.value or not r_label.value.strip():
                    ui.notify('Veuillez renseigner un nom de rôle.', type='warning')
                    return
                settings_mgr.update_role(role_id, {
                    "label": r_label.value.strip(),
                    "color": r_color_select.value,
                    "default_pct": float(r_pct.value or 10)
                })
                dialog.close()
                ui.notify(f'Rôle "{r_label.value}" mis à jour !', type='positive')
                render_workshop_tab.refresh()
                render_roles_legend.refresh()
                render_accordion_list.refresh()
            ui.button('Enregistrer', on_click=do_save_role).props('color=primary')
    dialog.open()

def confirm_delete_role(role_id: str, label: str):
    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl'):
        ui.label(f'Supprimer le rôle "{label}" ?').classes('text-base font-bold text-slate-900')
        ui.label('Les tables utilisant actuellement ce rôle seront automatiquement réassignées.').classes('text-xs text-slate-500 mb-4')
        with ui.row().classes('w-full justify-end gap-3'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_delete():
                try:
                    settings_mgr.delete_role(role_id)
                    dialog.close()
                    ui.notify(f'Rôle "{label}" supprimé.', type='info')
                    render_workshop_tab.refresh()
                    render_roles_legend.refresh()
                    render_accordion_list.refresh()
                except Exception as ex:
                    ui.notify(str(ex), type='negative')
            ui.button('Confirmer la suppression', on_click=do_delete).props('color=negative')
    dialog.open()

def open_add_table_dialog():
    roles = settings_mgr.get_roles()
    employees = settings_mgr.get_employees()
    current_count = len(settings_mgr.get_tables())
    next_num = current_count + 1

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl w-96 max-w-full'):
        ui.label('➕ Ajouter une Table de Travail').classes('text-base font-bold text-slate-900 mb-1')
        ui.label('Créez un nouveau poste de fabrication pour l\'atelier.').classes('text-xs text-slate-500 mb-4')

        t_name = ui.input('Nom de la table', value=f'Table {next_num}').props('outlined dense').classes('w-full mb-2')
        t_code = ui.input('Code court', value=f'T{next_num}').props('outlined dense').classes('w-full mb-2')
        t_role = ui.select(
            options={r["id"]: r["label"] for r in roles}, 
            value=roles[0]["id"] if roles else "coupe", 
            label="Premier rôle assigné"
        ).props('outlined dense').classes('w-full mb-2')
        t_emp = ui.select(
            options={e["id"]: e["name"] for e in employees},
            value=employees[0]["id"] if employees else "emp_1",
            label="Opérateur assigné"
        ).props('outlined dense').classes('w-full mb-2')
        t_desc = ui.input('Équipement / Machine', placeholder='Ex: Table d\'assemblage 4m').props('outlined dense').classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_add():
                if not t_name.value.strip():
                    ui.notify('Veuillez renseigner un nom de table.', type='warning')
                    return
                settings_mgr.add_table({
                    "name": t_name.value.strip(),
                    "code": t_code.value.strip() or f'T{next_num}',
                    "description": t_desc.value.strip() or 'Poste atelier',
                    "role_assignments": [
                        {"role_id": t_role.value, "employee_id": t_emp.value}
                    ]
                })
                dialog.close()
                ui.notify(f'"{t_name.value}" ajoutée avec succès !', type='positive')
                render_workshop_tab.refresh()
                render_employees_tab.refresh()
            ui.button('Créer la Table', on_click=do_add).props('color=primary')
    dialog.open()

# =========================================================================
# ACTIONS GLOBALES
# =========================================================================

def expand_all():
    for exp in state["expansions"].values():
        exp.value = True

def collapse_all():
    for exp in state["expansions"].values():
        exp.value = False

def confirm_delete(type_id: str, label: str):
    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl'):
        ui.label(f'Supprimer "{label}" ?').classes('text-base font-bold text-slate-900')
        ui.label('Cette action retirera ce modèle du catalogue.').classes('text-xs text-slate-500 mb-4')
        with ui.row().classes('w-full justify-end gap-3'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_delete():
                settings_mgr.delete_type(type_id)
                dialog.close()
                ui.notify(f'"{label}" a été supprimé.', type='info')
                render_category_tabs.refresh()
                render_accordion_list.refresh()
            ui.button('Confirmer la suppression', on_click=do_delete).props('color=negative')
    dialog.open()

def open_add_dialog():
    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl w-96 max-w-full'):
        ui.label('➕ Nouveau Modèle de Menuiserie').classes('text-base font-bold text-slate-900 mb-1')
        ui.label('Ajoutez un nouveau modèle à votre catalogue.').classes('text-xs text-slate-500 mb-4')

        new_label = ui.input('Nom du modèle', placeholder='Ex: H40 3 Vantaux').props('outlined dense').classes('w-full mb-2')
        new_gamme = ui.input('Gamme', placeholder='Ex: H40 3V').props('outlined dense').classes('w-full mb-2')
        new_cat = ui.select(
            options=[c["id"] for c in CATEGORIES if c["id"] != "ALL"], 
            value="CAT-F - Ouvrant", 
            label="Catégorie"
        ).props('outlined dense').classes('w-full mb-2')
        new_time = ui.number('Temps moyen (min)', value=75, min=5, max=999, step=5).props('outlined dense suffix="min"').classes('w-full mb-3')
        new_joint = ui.checkbox('Comporte Joint Vitrage', value=True).classes('mb-4 text-xs font-semibold')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_add():
                if not new_label.value or not new_label.value.strip():
                    ui.notify('Veuillez renseigner un nom de modèle.', type='warning')
                    return
                settings_mgr.add_type({
                    "label": new_label.value.strip(),
                    "gamme": new_gamme.value.strip() or "Standard",
                    "categorie": new_cat.value,
                    "has_joint_vitrage": new_joint.value,
                    "temps_moyen_min": float(new_time.value or 60.0)
                })
                dialog.close()
                ui.notify('Nouveau modèle ajouté avec succès !', type='positive')
                render_category_tabs.refresh()
                render_accordion_list.refresh()
            ui.button('Ajouter ce modèle', on_click=do_add).props('color=primary')
    dialog.open()

def confirm_reset():
    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-xl'):
        ui.label('🔄 Rétablir les données d\'origine ?').classes('text-base font-bold text-slate-900')
        ui.label('Cette action réinitialisera les 32 modèles du catalogue, les rôles, les tables et les employés par défaut.').classes('text-xs text-slate-500 mb-4')
        with ui.row().classes('w-full justify-end gap-3'):
            ui.button('Annuler', on_click=dialog.close).props('flat color=grey')
            def do_reset():
                settings_mgr.reset_to_defaults()
                dialog.close()
                ui.notify('Catalogue, rôles, tables et employés réinitialisés !', type='info')
                render_category_tabs.refresh()
                render_accordion_list.refresh()
                render_workshop_tab.refresh()
                render_roles_legend.refresh()
                render_employees_tab.refresh()
            ui.button('Rétablir les données d\'origine', on_click=do_reset).props('color=warning')
    dialog.open()

# =========================================================================
# PAGE PRINCIPALE AVEC TROIS SOUS-ONGLETS
# =========================================================================

@ui.page('/')
def main_page():
    # En-tête Navigation Supérieure
    with ui.header().classes('bg-white border-b border-slate-200 px-6 py-2.5 items-center justify-between text-slate-800 shadow-2xs'):
        with ui.row().classes('items-center gap-3'):
            with ui.avatar(color='blue-1', text_color='blue-8', icon='settings', size='md'):
                pass
            with ui.column().classes('gap-0'):
                with ui.row().classes('items-center gap-2'):
                    ui.label('SuiviPRO').classes('text-base font-extrabold text-slate-900 tracking-tight')
                    ui.label('Réglages & Configuration Atelier').classes('text-2xs font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full')
                ui.label('Modèles de Fenêtres, Tables Multi-Rôles et Équipe d\'Atelier').classes('text-2xs text-slate-500 font-medium')

        with ui.row().classes('items-center gap-2'):
            ui.button('🔄 Rétablir Réglages Usine', on_click=confirm_reset).props('outline color=grey size=sm').classes('font-medium text-xs')

    # Conteneur Principal
    with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-3'):
        # Barre d'Onglets de Navigation (3 Sous-onglets)
        with ui.tabs().classes('w-full bg-white border border-slate-200 rounded-xl p-1 shadow-2xs text-slate-600') as tabs:
            tab_models = ui.tab('tab_models', label='🪟 Modèles & Temps Cibles', icon='window').classes('font-bold')
            tab_workshop = ui.tab('tab_workshop', label='🏗️ Tables & Rôles Atelier', icon='table_restaurant').classes('font-bold')
            tab_employees = ui.tab('tab_employees', label='👥 Employés d\'Atelier', icon='badge').classes('font-bold')

        # Panneaux de contenu
        with ui.tab_panels(tabs, value='tab_models').classes('w-full bg-transparent'):
            # --- Panneau 1 : Modèles & Ventilation ---
            with ui.tab_panel('tab_models').classes('p-0 pt-2'):
                with ui.row().classes('w-full items-center justify-between mb-2 flex-wrap gap-2'):
                    with ui.column().classes('gap-0'):
                        ui.label('Catalogue des 32 Modèles & Ventilation par Poste').classes('text-lg font-extrabold text-slate-900')
                        ui.label('Configurez le temps moyen théorique et activez/désactivez les postes requis pour chaque modèle.').classes('text-xs text-slate-500')
                    
                    ui.button('➕ Nouveau Modèle', on_click=open_add_dialog).props('color=primary size=sm').classes('font-bold shadow-xs text-xs')

                render_roles_legend()
                render_category_tabs()

                with ui.row().classes('w-full items-center mb-3'):
                    search_input = ui.input(
                        placeholder='🔍 Rechercher un modèle, gamme (ex: H31, H40, H52, H68t, Coulissant, Plinthe)...'
                    ).props('outlined dense clearable').classes('w-full bg-white rounded-lg shadow-2xs')
                    
                    def on_search_change(e):
                        state["search"] = e.value or ""
                        render_accordion_list.refresh()

                    search_input.on('update:model-value', on_search_change)

                render_accordion_list()

            # --- Panneau 2 : Organisation d'Atelier & Tables Multi-Rôles ---
            with ui.tab_panel('tab_workshop').classes('p-0 pt-2'):
                render_workshop_tab()

            # --- Panneau 3 : Employés d'Atelier ---
            with ui.tab_panel('tab_employees').classes('p-0 pt-2'):
                render_employees_tab()


# =========================================================================
# PAGE BORNE DE POINTAGE FACE ID (ACCESSIBLE VIA QR CODE & TABLETTE ATELIER)
# =========================================================================

@ui.page('/pointage')
def pointage_kiosk_page():
    # État local de la borne
    kiosk_state = {
        "admin_unlocked": False,
        "last_recognized": None
    }

    # Style spécifique Kiosk (plein écran optimisé tablette & mobile)
    ui.add_head_html("""
    <style>
        .scan-container {
            position: relative;
            width: 100%;
            max-width: 480px;
            aspect-ratio: 4 / 3;
            background: #0F172A;
            border-radius: 1.5rem;
            overflow: hidden;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }
        .scan-oval {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 220px;
            height: 280px;
            border: 2px dashed #3B82F6;
            border-radius: 50%;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.35);
            animation: pulse-border 2.5s infinite ease-in-out;
            pointer-events: none;
        }
        @keyframes pulse-border {
            0%, 100% { border-color: #3B82F6; box-shadow: 0 0 15px rgba(59, 130, 246, 0.3); }
            50% { border-color: #10B981; box-shadow: 0 0 25px rgba(16, 185, 129, 0.6); }
        }
        .scan-beam {
            position: absolute;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, transparent, #3B82F6, #10B981, transparent);
            box-shadow: 0 0 12px #3B82F6;
            animation: scan-move 3s infinite ease-in-out;
            pointer-events: none;
        }
        @keyframes scan-move {
            0% { top: 15%; opacity: 0.2; }
            50% { top: 85%; opacity: 1; }
            100% { top: 15%; opacity: 0.2; }
        }
    </style>
    """)

    # En-tête de la borne
    with ui.header().classes('bg-white border-b border-slate-200 px-6 py-3 items-center justify-between text-slate-800 shadow-2xs'):
        with ui.row().classes('items-center gap-3'):
            with ui.avatar(color='blue-1', text_color='blue-8', icon='qr_code_scanner', size='md'):
                pass
            with ui.column().classes('gap-0'):
                ui.label('SuiviPRO — Borne de Pointage Atelier').classes('text-base font-extrabold text-slate-900 tracking-tight')
                ui.label('Reconnaissance Faciale Face ID & Présence en Direct').classes('text-2xs text-slate-500 font-medium')

        with ui.row().classes('items-center gap-2'):
            # Horloge en direct
            clock_label = ui.label('08:00:00').classes('text-sm font-bold font-mono bg-slate-100 text-slate-800 px-3 py-1 rounded-lg border border-slate-200')
            ui.timer(1.0, lambda: clock_label.set_text(datetime.now().strftime("%H:%M:%S")))

            # Bouton Accès Administrateur Kiosk
            def open_admin_pin_modal():
                with ui.dialog() as pin_dialog, ui.card().classes('p-6 bg-white rounded-2xl w-80 max-w-full text-center items-center gap-3 shadow-xl'):
                    ui.icon('lock', size='md').classes('text-blue-600')
                    ui.label('Accès Administrateur Borne').classes('text-base font-bold text-slate-900')
                    ui.label('Entrez le code PIN pour gérer ou créer un employé sur place.').classes('text-xs text-slate-500 mb-2')
                    
                    pin_input = ui.input(placeholder='Code PIN (ex: 1234)', password=True).props('outlined dense autofocus maxlength=8').classes('w-full text-center font-mono text-lg')

                    with ui.row().classes('w-full justify-end gap-2 pt-2'):
                        ui.button('Annuler', on_click=pin_dialog.close).props('flat color=grey')
                        def check_pin():
                            if settings_mgr.verify_admin_pin(pin_input.value or ""):
                                pin_dialog.close()
                                ui.notify('Mode Administrateur déverrouillé !', type='positive')
                                open_kiosk_admin_create_dialog()
                            else:
                                ui.notify('Code PIN incorrect.', type='negative')
                        ui.button('Déverrouiller', on_click=check_pin).props('color=primary').classes('font-bold')
                pin_dialog.open()

            ui.button('🔒 Accès Admin', on_click=open_admin_pin_modal).props('outline color=grey size=sm').classes('font-bold text-xs')
            ui.button('🪟 Réglages Atelier', on_click=lambda: ui.navigate.to('/')).props('color=primary size=sm').classes('font-bold text-xs shadow-xs')

    # Contenu Principal de la Borne
    with ui.column().classes('w-full max-w-2xl mx-auto p-4 md:p-6 items-center gap-4'):
        # Zone de statut et notification en temps réel
        status_card = ui.card().classes('w-full bg-blue-50 border border-blue-200 rounded-2xl p-4 shadow-2xs text-center items-center gap-1')
        with status_card:
            status_icon = ui.icon('face', size='md').classes('text-blue-600 mb-0.5')
            status_title = ui.label('Positionnez votre visage dans le cadre pour pointer').classes('text-sm font-bold text-slate-800')
            status_desc = ui.label('La reconnaissance biométrique enregistrera automatiquement votre arrivée ou votre départ.').classes('text-xs text-slate-500')

        # Viseur Biométrique / Caméra
        with ui.element('div').classes('scan-container flex items-center justify-center relative'):
            # Flux vidéo HTML5 de la caméra web
            ui.html('<video id="kiosk-camera" autoplay playsinline muted style="width: 100%; height: 100%; object-fit: cover;"></video>')
            
            # Cadre ovale biométrique et rayon laser animé
            ui.element('div').classes('scan-oval')
            ui.element('div').classes('scan-beam')

            # Bouton d'activation si le navigateur bloque l'autoplay
            async def manual_start_cam():
                await ui.run_javascript("window.suiviCam.start('kiosk-camera', 'kiosk-cam-status')")
                kiosk_start_btn.classes(add='hidden')

            kiosk_start_btn = ui.button('📷 Démarrer / Autoriser la Caméra', on_click=manual_start_cam).props('color=primary size=md icon=videocam').classes('absolute font-bold shadow-lg')

            # Badge superposition
            with ui.element('div').classes('absolute bottom-3 left-4 right-4 flex items-center justify-between text-white text-2xs font-mono bg-slate-900/70 backdrop-blur-xs px-3 py-1.5 rounded-lg'):
                ui.html('<div id="kiosk-cam-status" class="text-emerald-400 font-bold">● CAMERA INITIALISATION...</div>')
                ui.label('ALGO FACE-ID v2.4').classes('text-slate-300')

        # Démarrage automatique au chargement
        ui.timer(0.3, lambda: ui.run_javascript("""
            window.suiviCam.start('kiosk-camera', 'kiosk-cam-status').then(ok => {
                if (ok) {
                    const btn = document.querySelector('.scan-container button');
                    if (btn) btn.style.display = 'none';
                }
            });
        """), once=True)

        # Sélecteur rapide / Bouton de Scan Face ID
        enrolled_employees = [e for e in settings_mgr.get_employees() if e.get("face_id_enrolled", True)]
        emp_options = {e["id"]: f"{e['name']} ({e.get('code', '')}) - {e.get('specialty', '')}" for e in enrolled_employees}

        with ui.card().classes('w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs gap-3'):
            ui.label('📸 Reconnaissance & Validation du Pointage :').classes('text-xs font-bold text-slate-600 uppercase tracking-wider')

            with ui.row().classes('w-full items-center gap-2 flex-wrap'):
                selected_emp = ui.select(
                    options=emp_options,
                    value=list(emp_options.keys())[0] if emp_options else None,
                    label="Opérateur devant la caméra"
                ).props('outlined dense').classes('flex-1 bg-white')

                @ui.refreshable
                def render_kiosk_recent():
                    recent_p = settings_mgr.get_recent_punches(limit=5)
                    if recent_p:
                        with ui.column().classes('w-full gap-1.5'):
                            for p in recent_p:
                                with ui.row().classes('w-full items-center justify-between bg-slate-50 border border-slate-100 rounded-lg p-2 px-3 text-xs'):
                                    with ui.row().classes('items-center gap-2'):
                                        if p["punch_type"] == "IN":
                                            ui.label('🟢 Entrée').classes('text-3xs font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded')
                                        else:
                                            ui.label('🔴 Sortie').classes('text-3xs font-bold text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded')
                                        ui.label(p.get("employee_name")).classes('font-bold text-slate-800')
                                    with ui.row().classes('items-center gap-2'):
                                        if p.get("confidence"):
                                            ui.label(f'{int(p["confidence"] * 100)}% Face ID').classes('text-3xs text-slate-400 font-mono')
                                        ui.label(p.get("time_short")).classes('font-mono font-bold text-slate-500')
                    else:
                        ui.label('Aucun passage aujourd\'hui pour le moment.').classes('text-xs text-slate-400 italic')

                async def trigger_face_scan():
                    if not selected_emp.value:
                        ui.notify('Veuillez sélectionner un opérateur.', type='warning')
                        return
                    
                    emp_obj = next((e for e in settings_mgr.get_employees() if e["id"] == selected_emp.value), None)
                    if not emp_obj:
                        return

                    # 1. Capture de la photo en direct depuis la caméra
                    snapshot = await ui.run_javascript("window.suiviCam.capture('kiosk-camera')")
                    if not snapshot or len(str(snapshot)) < 150:
                        ui.notify('Caméra non active ou image vide. Allumez la caméra d\'abord.', type='warning')
                        return

                    # 2. Vérification biométrique réelle entre le visage devant la caméra et le profil enregistré
                    verif = settings_mgr.verify_face_match(emp_obj["id"], snapshot, threshold=65.0)

                    if not verif["match"]:
                        # ❌ Visage différent ou profil inconnu -> REFUS DE POINTAGE STRICT
                        status_card.classes('bg-rose-50 border-rose-300', remove='bg-blue-50 border-blue-200 bg-emerald-50 border-emerald-300')
                        status_icon.props('name=cancel').classes('text-rose-600', remove='text-blue-600 text-emerald-600')
                        status_title.set_text('❌ Visage Non Reconnu — Pointage Refusé !')
                        status_desc.set_text(verif["reason"])

                        ui.notify(
                            verif["reason"], 
                            type='negative', 
                            position='top',
                            close_button=True,
                            duration=7000
                        )
                        return

                    # ✅ Visage conforme -> Validation et carillon sonore
                    punch_res = verif["punch"]
                    await ui.run_javascript("window.suiviCam.playChime()")

                    is_in = punch_res["punch_type"] == "IN"
                    act_label = "ARRIVÉE / PRISE DE POSTE" if is_in else "DÉPART / FIN DE POSTE"

                    # Mise à jour visuelle du bandeau en vert
                    status_card.classes('bg-emerald-50 border-emerald-300', remove='bg-blue-50 border-blue-200 bg-rose-50 border-rose-300')
                    status_icon.props('name=check_circle').classes('text-emerald-600', remove='text-blue-600 text-rose-600')
                    status_title.set_text(f'✅ {emp_obj["name"]} ({emp_obj.get("code")}) — {act_label} Validée !')
                    status_desc.set_text(f'Pointage horodaté à {punch_res["time_short"]} • Indice de correspondance Face ID : {verif["score"]}%')

                    ui.notify(
                        f'Pointage {act_label} validé pour {emp_obj["name"]} (Score Face ID : {verif["score"]}%) !', 
                        type='positive', 
                        position='top',
                        close_button=True
                    )
                    render_kiosk_recent.refresh()

                ui.button('📸 Scanner mon Visage & Pointer', on_click=trigger_face_scan).props('color=primary size=md icon=camera_alt').classes('font-bold shadow-xs px-4')

        # Panneau des derniers pointages sur la borne
        with ui.card().classes('w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs'):
            ui.label('📋 Derniers passages à cette borne :').classes('text-xs font-bold text-slate-500 uppercase tracking-wider mb-2')
            render_kiosk_recent()


def open_kiosk_admin_create_dialog():
    """Dialogue Administrateur sur la Borne pour créer un employé et capturer son Face ID sur place"""
    next_num = len(settings_mgr.get_employees()) + 1
    kiosk_captured = {"data": None}

    with ui.dialog() as dialog, ui.card().classes('p-6 bg-white rounded-2xl w-[440px] max-w-full shadow-2xl'):
        ui.icon('badge', size='md').classes('text-blue-600')
        ui.label('👑 Création Nouvel Employé (Borne Atelier)').classes('text-base font-extrabold text-slate-900')
        ui.label('Enregistrez un opérateur et capturez son Face ID directement depuis la tablette.').classes('text-xs text-slate-500 mb-3')

        new_name = ui.input('Nom et prénom', placeholder='Ex: Alexandre Dumas').props('outlined dense').classes('w-full mb-2')
        new_code = ui.input('Matricule / Code', value=f'EMP-{next_num:02d}').props('outlined dense').classes('w-full mb-2')
        new_spec = ui.input('Spécialité / Métier', placeholder='Ex: Débit, Assemblage, Vitrage...').props('outlined dense').classes('w-full mb-2')
        new_phone = ui.input('Téléphone', placeholder='Ex: 06 00 00 00 00').props('outlined dense').classes('w-full mb-3')

        # Cadre caméra Kiosk
        with ui.card().classes('w-full p-3 bg-slate-50 border border-slate-200 rounded-xl items-center gap-2 mb-3'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Capture Visage Face ID').classes('text-xs font-bold text-slate-800')
                ui.html('<div id="kiosk-add-status" class="text-3xs font-mono text-slate-500 font-semibold">● Prêt</div>')

            with ui.element('div').classes('w-full relative rounded-lg overflow-hidden bg-slate-950 flex flex-col items-center justify-center').style('height: 180px;'):
                ui.html('<video id="kiosk-add-cam" autoplay playsinline muted style="width: 100%; height: 180px; object-fit: cover;"></video>')
                ui.html('''
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 110px; height: 140px; border: 2px dashed #3B82F6; border-radius: 50%; pointer-events: none; box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);"></div>
                ''')
                kiosk_add_preview = ui.image('').classes('absolute inset-0 w-full h-full object-cover hidden rounded-lg')

            with ui.row().classes('w-full items-center justify-center gap-2'):
                async def start_kiosk_add_cam():
                    await ui.run_javascript("window.suiviCam.start('kiosk-add-cam', 'kiosk-add-status')")
                    kiosk_add_preview.classes(add='hidden')

                async def capture_kiosk_add_photo():
                    photo_b64 = await ui.run_javascript("window.suiviCam.capture('kiosk-add-cam')")
                    if photo_b64 and len(str(photo_b64)) > 100:
                        kiosk_captured["data"] = photo_b64
                        kiosk_add_preview.set_source(photo_b64)
                        kiosk_add_preview.classes(remove='hidden')
                        ui.notify('Photo Face ID capturée avec succès !', type='positive')
                    else:
                        started = await ui.run_javascript("window.suiviCam.start('kiosk-add-cam', 'kiosk-add-status')")
                        if not started:
                            ui.notify('Activez la caméra ou importez une photo ci-dessous.', type='warning')
                        else:
                            ui.notify('Caméra allumée ! Re-cliquez sur "Prendre Photo".', type='info')

                ui.button('📷 Allumer Caméra', on_click=start_kiosk_add_cam).props('outline size=xs color=primary').classes('font-bold text-2xs')
                ui.button('📸 Prendre Photo Face ID', on_click=capture_kiosk_add_photo).props('color=primary size=xs').classes('font-bold text-2xs shadow-xs')

        # Option import alternatif
        def handle_kiosk_upload(e):
            import base64
            b64_content = base64.b64encode(e.content.read()).decode('utf-8')
            mime = e.type or 'image/jpeg'
            data_url = f"data:{mime};base64,{b64_content}"
            kiosk_captured["data"] = data_url
            kiosk_add_preview.set_source(data_url)
            kiosk_add_preview.classes(remove='hidden')
            ui.notify('Photo importée avec succès !', type='positive')

        with ui.expansion('Ou importer une photo de profil...', icon='folder').classes('w-full text-2xs text-slate-500 border border-slate-200 rounded-lg mb-3'):
            ui.upload(on_upload=handle_kiosk_upload, max_files=1).props('dense outlined accept="image/*"').classes('w-full text-2xs')

        with ui.row().classes('w-full justify-end gap-2'):
            def on_kiosk_add_close():
                ui.run_javascript("window.suiviCam.stop('kiosk-add-cam')")
                dialog.close()

            ui.button('Fermer', on_click=on_kiosk_add_close).props('flat color=grey')

            def do_admin_add():
                if not new_name.value or not new_name.value.strip():
                    ui.notify('Veuillez renseigner le nom de l\'employé.', type='warning')
                    return
                
                settings_mgr.add_employee({
                    "name": new_name.value.strip(),
                    "code": new_code.value.strip() or f'EMP-{next_num:02d}',
                    "specialty": new_spec.value.strip() or 'Opérateur atelier',
                    "phone": new_phone.value.strip(),
                    "active": True,
                    "presence_status": "PRESENT",
                    "face_id_enrolled": True,
                    "face_photo": kiosk_captured["data"] or "data:image/png;base64,kiosk_face"
                })
                on_kiosk_add_close()
                ui.notify(f'Employé "{new_name.value}" créé avec Face ID activé !', type='positive', position='top')
                ui.navigate.to('/pointage')

            ui.button('Enregistrer & Activer', on_click=do_admin_add).props('color=primary').classes('font-bold shadow-xs')

    dialog.open()
    ui.timer(0.2, lambda: ui.run_javascript("window.suiviCam.start('kiosk-add-cam', 'kiosk-add-status')"), once=True)



if __name__ in {"__main__", "__mp_main__"}:
    print("=" * 65)
    print("🚀 Démarrage SuiviPRO : Réglages Modèles, Tables & Employés Atelier")
    print("=" * 65)
    ui.run(
        host='0.0.0.0', 
        port=8000, 
        title='SuiviPRO - Réglages & Organisation Atelier', 
        reload=False,
        show=False
    )


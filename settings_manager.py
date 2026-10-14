"""
Gestionnaire des Réglages Atelier - Étape 1 & Organisation Atelier
Types de menuiseries réels, ventilation par rôle, tables multi-rôles et gestion des employés d'atelier.
"""

import os
import json
import io
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import qrcode
except ImportError:
    qrcode = None

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Les 5 rôles clés de production
PRODUCTION_ROLES = [
    {"id": "coupe", "label": "Coupe / Débit", "color": "#3B82F6", "default_pct": 15, "icon": "content_cut"},
    {"id": "grugage", "label": "Grugage / Usinage", "color": "#8B5CF6", "default_pct": 20, "icon": "build"},
    {"id": "assemblage", "label": "Assemblage Cadres & Ouvrants", "color": "#F59E0B", "default_pct": 40, "icon": "handyman"},
    {"id": "vitrage", "label": "Vitrage & Joints", "color": "#06B6D4", "default_pct": 15, "icon": "window"},
    {"id": "emballage", "label": "Contrôle & Emballage", "color": "#10B981", "default_pct": 10, "icon": "inventory"}
]

# Les 6 employés de référence de l'atelier avec statut de pointage et Face ID
DEFAULT_EMPLOYEES = [
    {
        "id": "emp_1",
        "name": "Karim Benali",
        "code": "EMP-01",
        "specialty": "Opérateur Débit & Tronçonneuse",
        "phone": "06 12 34 56 78",
        "active": True,
        "presence_status": "PRESENT",
        "last_punch_at": "08:00:12",
        "face_id_enrolled": True
    },
    {
        "id": "emp_2",
        "name": "Moussa Traoré",
        "code": "EMP-02",
        "specialty": "Technicien Usinage & Grugage",
        "phone": "06 23 45 67 89",
        "active": True,
        "presence_status": "PRESENT",
        "last_punch_at": "08:05:44",
        "face_id_enrolled": True
    },
    {
        "id": "emp_3",
        "name": "Thomas Mercier",
        "code": "EMP-03",
        "specialty": "Monteur Assembleur Cadres Dormants",
        "phone": "06 34 56 78 90",
        "active": True,
        "presence_status": "PRESENT",
        "last_punch_at": "08:12:05",
        "face_id_enrolled": True
    },
    {
        "id": "emp_4",
        "name": "Lucas Martin",
        "code": "EMP-04",
        "specialty": "Monteur Ouvrants & Quincaillerie",
        "phone": "06 45 67 89 01",
        "active": True,
        "presence_status": "ABSENT",
        "last_punch_at": None,
        "face_id_enrolled": True
    },
    {
        "id": "emp_5",
        "name": "Youssef Alami",
        "code": "EMP-05",
        "specialty": "Poseur Vitrage, Joints & Parecloses",
        "phone": "06 56 78 90 12",
        "active": True,
        "presence_status": "PRESENT",
        "last_punch_at": "08:15:30",
        "face_id_enrolled": True
    },
    {
        "id": "emp_6",
        "name": "Sofiane B.",
        "code": "EMP-06",
        "specialty": "Contrôleur Qualité & Conditionnement",
        "phone": "06 67 89 01 23",
        "active": True,
        "presence_status": "BREAK",
        "last_punch_at": "12:00:15",
        "face_id_enrolled": True
    }
]

# Les 6 tables standards configurées par défaut dans l'atelier (chaque table supporte plusieurs rôles avec employés dédiés)
DEFAULT_TABLES = [
    {
        "id": "table_1",
        "name": "Table 1",
        "code": "T1",
        "description": "Poste débit profilés & tronçonneuse aluminium double tête",
        "active": True,
        "role_assignments": [
            {"role_id": "coupe", "employee_id": "emp_1"}
        ]
    },
    {
        "id": "table_2",
        "name": "Table 2",
        "code": "T2",
        "description": "Centre d'usinage, grugeuse & pantographe serrures",
        "active": True,
        "role_assignments": [
            {"role_id": "grugage", "employee_id": "emp_2"}
        ]
    },
    {
        "id": "table_3",
        "name": "Table 3",
        "code": "T3",
        "description": "Sertissage des angles & montage des cadres dormants",
        "active": True,
        "role_assignments": [
            {"role_id": "assemblage", "employee_id": "emp_3"}
        ]
    },
    {
        "id": "table_4",
        "name": "Table 4",
        "code": "T4",
        "description": "Assemblage des ouvrants, battants & quincaillerie multipoints",
        "active": True,
        "role_assignments": [
            {"role_id": "assemblage", "employee_id": "emp_4"}
        ]
    },
    {
        "id": "table_5",
        "name": "Table 5",
        "code": "T5",
        "description": "Pose du vitrage, calage, joints d'étanchéité & parecloses",
        "active": True,
        "role_assignments": [
            {"role_id": "vitrage", "employee_id": "emp_5"}
        ]
    },
    {
        "id": "table_6",
        "name": "Table 6",
        "code": "T6",
        "description": "Contrôle qualité final, protection d'angles & conditionnement",
        "active": True,
        "role_assignments": [
            {"role_id": "emballage", "employee_id": "emp_6"}
        ]
    }
]

# Les 32 modèles réels issus du catalogue de l'atelier
CATALOG_JOINERY_TYPES = [
    # --- Coulissants (CAT-F - Coulissant) ---
    {
        "id": "h31_2ouv_sv",
        "label": "H31 2 Ouvrant SV",
        "gamme": "H31 2Ouv SV",
        "categorie": "CAT-F - Coulissant",
        "has_joint_vitrage": True,
        "composants_count": 16,
        "description": "Coulissant H31 2 ouvrants Simple Vitrage",
        "temps_moyen_min": 75.0,
        "ratios": {"coupe": 15, "grugage": 15, "assemblage": 45, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h31_2ouv_dv",
        "label": "H31 2 Ouvrant DV",
        "gamme": "H31 2Ouv DV",
        "categorie": "CAT-F - Coulissant",
        "has_joint_vitrage": True,
        "composants_count": 16,
        "description": "Coulissant H31 2 ouvrants Double Vitrage",
        "temps_moyen_min": 80.0,
        "ratios": {"coupe": 15, "grugage": 15, "assemblage": 45, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h36_dv_2ouv",
        "label": "H36 DV 2 Ouvrant",
        "gamme": "H36 2Ouv DV",
        "categorie": "CAT-F - Coulissant",
        "has_joint_vitrage": True,
        "composants_count": 16,
        "description": "Coulissant H36 2 ouvrants Double Vitrage",
        "temps_moyen_min": 85.0,
        "ratios": {"coupe": 15, "grugage": 15, "assemblage": 45, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h36_3panneau_dv_3r",
        "label": "H36 3 PANNEAU DV 3R",
        "gamme": "H36 trois panneaux dv",
        "categorie": "CAT-F - Coulissant",
        "has_joint_vitrage": True,
        "composants_count": 21,
        "description": "Coulissant H36 3 panneaux Double Vitrage 3 rails",
        "temps_moyen_min": 130.0,
        "ratios": {"coupe": 15, "grugage": 15, "assemblage": 45, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h48t_do",
        "label": "H48T DO",
        "gamme": "H48T DO",
        "categorie": "CAT-F - Coulissant",
        "has_joint_vitrage": True,
        "composants_count": 24,
        "description": "Coulissant H48T Double Ouvrant",
        "temps_moyen_min": 110.0,
        "ratios": {"coupe": 15, "grugage": 15, "assemblage": 45, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h48t_3vantaux",
        "label": "H48T 3 vantaux",
        "gamme": "H48T trois panneaux",
        "categorie": "CAT-F - Coulissant",
        "has_joint_vitrage": True,
        "composants_count": 22,
        "description": "Coulissant H48T 3 vantaux grande dimension",
        "temps_moyen_min": 140.0,
        "ratios": {"coupe": 15, "grugage": 15, "assemblage": 45, "vitrage": 15, "emballage": 10}
    },

    # --- Fenêtres Ouvrantes (CAT-F - Ouvrant) ---
    {
        "id": "h40_1v",
        "label": "H40 1 Vantail",
        "gamme": "H40 1V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 17,
        "description": "Fenêtre ouvrante H40 1 vantail",
        "temps_moyen_min": 55.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h40_2v",
        "label": "H40 2 Vantaux",
        "gamme": "H40 2V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 17,
        "description": "Fenêtre ouvrante H40 2 vantaux",
        "temps_moyen_min": 70.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h40_vasistas",
        "label": "H40 VASISTAS",
        "gamme": "H40 Vasistas",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 12,
        "description": "Châssis à soufflet / Vasistas H40",
        "temps_moyen_min": 45.0,
        "ratios": {"coupe": 20, "grugage": 15, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h52_1v",
        "label": "H52 1 VANTAIL",
        "gamme": "H52 1V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 17,
        "description": "Fenêtre ouvrante série H52 1 vantail",
        "temps_moyen_min": 60.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "h52_2v",
        "label": "H52 2 Vantaux",
        "gamme": "H52 2V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 18,
        "description": "Fenêtre ouvrante série H52 2 vantaux",
        "temps_moyen_min": 75.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "fenetre_1v_h68t",
        "label": "Fenetre Un vantail H68t",
        "gamme": "H68t 1V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 14,
        "description": "Fenêtre H68t ouvrant 1 vantail à rupture de pont thermique",
        "temps_moyen_min": 65.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "fenetre_2v_h68t",
        "label": "Fenetre 2 vantaux H68t",
        "gamme": "H68t 2V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 18,
        "description": "Fenêtre H68t ouvrant 2 vantaux à rupture de pont thermique",
        "temps_moyen_min": 80.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "vasistas_h52",
        "label": "Vasistas H52",
        "gamme": "H52 1V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 12,
        "description": "Châssis à soufflet / Vasistas H52",
        "temps_moyen_min": 45.0,
        "ratios": {"coupe": 20, "grugage": 15, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "e_75",
        "label": "E-75",
        "gamme": "E-75",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 15,
        "description": "Série E-75 profil ouvrant renforcé",
        "temps_moyen_min": 70.0,
        "ratios": {"coupe": 15, "grugage": 20, "assemblage": 40, "vitrage": 15, "emballage": 10}
    },

    # --- Portes Battantes & Plinthes (CAT-F - Ouvrant) ---
    {
        "id": "porte_1v_40",
        "label": "Porte un vantail 40",
        "gamme": "P H40 1V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 13,
        "description": "Porte d'entrée 1 vantail série H40",
        "temps_moyen_min": 75.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_2v_h40",
        "label": "Porte deux vantail H40",
        "gamme": "P H40 2V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 18,
        "description": "Porte d'entrée double vantail série H40",
        "temps_moyen_min": 95.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_1v_h40_plinthe",
        "label": "Porte un vantail H40 Plinthe",
        "gamme": "P H40 1V Plinthe",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 17,
        "description": "Porte 1 vantail H40 avec plinthe basse",
        "temps_moyen_min": 85.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_2v_h40_plinthe",
        "label": "Porte deux vantaux H40 Plinthe",
        "gamme": "P H40 2V Plinthe",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 19,
        "description": "Porte 2 vantaux H40 avec plinthe basse",
        "temps_moyen_min": 105.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_1v_h52",
        "label": "Porte un vantail H52",
        "gamme": "P H52 1V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 17,
        "description": "Porte 1 vantail profil lourd série H52",
        "temps_moyen_min": 85.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_2v_h52",
        "label": "Porte deux vantaux H52",
        "gamme": "P H52 2V",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 18,
        "description": "Porte double ouvrant profil lourd série H52",
        "temps_moyen_min": 110.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_1v_h52_plinthe",
        "label": "Porte un vantail H52 Plinthe",
        "gamme": "P H52 1V Plinthe",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 14,
        "description": "Porte 1 vantail H52 avec plinthe basse",
        "temps_moyen_min": 90.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_2v_h52_plinthe",
        "label": "Porte deux vantaux H52 Plinthe",
        "gamme": "P H52 2V Plinthe",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 19,
        "description": "Porte 2 vantaux H52 avec plinthe basse",
        "temps_moyen_min": 115.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },
    {
        "id": "porte_serrure_h68t",
        "label": "Porte Serrure H68t",
        "gamme": "P H68t",
        "categorie": "CAT-F - Ouvrant",
        "has_joint_vitrage": True,
        "composants_count": 19,
        "description": "Porte grand trafic serrure sécurité série H68t",
        "temps_moyen_min": 100.0,
        "ratios": {"coupe": 15, "grugage": 25, "assemblage": 35, "vitrage": 15, "emballage": 10}
    },

    # --- Châssis Fixes (CAT-F - Fixe) ---
    {
        "id": "h40_fix",
        "label": "H40 FIX",
        "gamme": "H40 FIX",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 9,
        "description": "Châssis fixe vitré série H40",
        "temps_moyen_min": 35.0,
        "ratios": {"coupe": 20, "grugage": 10, "assemblage": 35, "vitrage": 25, "emballage": 10}
    },
    {
        "id": "h52_fix",
        "label": "H52 FIX",
        "gamme": "H52 FIX",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 10,
        "description": "Châssis fixe vitré série H52",
        "temps_moyen_min": 40.0,
        "ratios": {"coupe": 20, "grugage": 10, "assemblage": 35, "vitrage": 25, "emballage": 10}
    },
    {
        "id": "h68t_fix",
        "label": "H68t FIX",
        "gamme": "Fix H68t",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 8,
        "description": "Châssis fixe vitré H68t à rupture thermique",
        "temps_moyen_min": 40.0,
        "ratios": {"coupe": 20, "grugage": 10, "assemblage": 35, "vitrage": 25, "emballage": 10}
    },

    # --- Précadres (CAT-F - Fixe) ---
    {
        "id": "pres_cadre",
        "label": "Pres Cadre",
        "gamme": "Precadre",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 7,
        "description": "Précadre standard de pose",
        "temps_moyen_min": 30.0,
        "ratios": {"coupe": 25, "grugage": 10, "assemblage": 45, "vitrage": 5, "emballage": 15}
    },
    {
        "id": "precadre_trav_h",
        "label": "Precadre Trav H",
        "gamme": "Precadre Trav H",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 7,
        "description": "Précadre avec traverse horizontale",
        "temps_moyen_min": 30.0,
        "ratios": {"coupe": 25, "grugage": 10, "assemblage": 45, "vitrage": 5, "emballage": 15}
    },
    {
        "id": "precadre_trav_v",
        "label": "Precadre Trav V",
        "gamme": "Precadre Trav V",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 7,
        "description": "Précadre avec montant / traverse verticale",
        "temps_moyen_min": 30.0,
        "ratios": {"coupe": 25, "grugage": 10, "assemblage": 45, "vitrage": 5, "emballage": 15}
    },
    {
        "id": "precadre_2_trav",
        "label": "Precadre 2 Trav",
        "gamme": "Precadre 2 Trav",
        "categorie": "CAT-F - Fixe",
        "has_joint_vitrage": True,
        "composants_count": 7,
        "description": "Précadre avec 2 traverses de renfort",
        "temps_moyen_min": 35.0,
        "ratios": {"coupe": 25, "grugage": 10, "assemblage": 45, "vitrage": 5, "emballage": 15}
    },

    # --- Spécial & Garde-corps ---
    {
        "id": "garde_corps_laila_1100",
        "label": "Garde corps laila 1100",
        "gamme": "Garde corps laila",
        "categorie": "CAT-Special - Garde Corps",
        "has_joint_vitrage": True,
        "composants_count": 12,
        "description": "Garde-corps aluminium Laila hauteur 1100 mm",
        "temps_moyen_min": 50.0,
        "ratios": {"coupe": 25, "grugage": 15, "assemblage": 45, "vitrage": 5, "emballage": 10}
    }
]

class SettingsManager:
    def __init__(self):
        self.joinery_types: List[Dict[str, Any]] = []
        self.tables: List[Dict[str, Any]] = []
        self.roles: List[Dict[str, Any]] = list(PRODUCTION_ROLES)
        self.employees: List[Dict[str, Any]] = [dict(e) for e in DEFAULT_EMPLOYEES]
        self.attendance_punches: List[Dict[str, Any]] = []
        self.kiosk_settings: Dict[str, Any] = {
            "admin_pin": "1234",
            "kiosk_name": "Borne Entrée Atelier",
            "qr_token": "kiosk_atelier_token"
        }
        self.face_credentials: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    types = data.get("joinery_types", [])
                    tables = data.get("tables", [])
                    roles = data.get("roles", [])
                    employees = data.get("employees", [])
                    
                    if types and len(types) > 0:
                        self.joinery_types = types
                    else:
                        self.joinery_types = [dict(t) for t in CATALOG_JOINERY_TYPES]
                        
                    if roles and len(roles) > 0:
                        self.roles = roles
                    else:
                        self.roles = list(PRODUCTION_ROLES)

                    if employees and len(employees) > 0:
                        self.employees = employees
                    else:
                        self.employees = [dict(e) for e in DEFAULT_EMPLOYEES]
                        
                    # Assurer que chaque employé a les champs de pointage et face ID
                    for e in self.employees:
                        if "presence_status" not in e:
                            e["presence_status"] = "PRESENT" if e.get("active", True) else "ABSENT"
                        if "last_punch_at" not in e:
                            e["last_punch_at"] = "08:00:00" if e.get("active", True) else None
                        if "face_id_enrolled" not in e:
                            e["face_id_enrolled"] = True

                    if tables and len(tables) > 0:
                        # Assurer la compatibilité avec le format role_assignments multi-rôles
                        for tb in tables:
                            if "role_assignments" not in tb or not isinstance(tb["role_assignments"], list):
                                old_role = tb.get("role_id", "assemblage")
                                tb["role_assignments"] = [{"role_id": old_role, "employee_id": self.employees[0]["id"]}]
                        self.tables = tables
                    else:
                        self.tables = [dict(tb) for tb in DEFAULT_TABLES]

                    self.attendance_punches = data.get("attendance_punches", [])
                    self.kiosk_settings = data.get("kiosk_settings", {
                        "admin_pin": "1234",
                        "kiosk_name": "Borne Entrée Atelier",
                        "qr_token": "kiosk_atelier_token"
                    })
                    self.face_credentials = data.get("face_credentials", {})
                    return
            except Exception as e:
                print(f"Erreur chargement réglages ({e}), réinitialisation...")
        
        self.joinery_types = [dict(t) for t in CATALOG_JOINERY_TYPES]
        self.tables = [dict(tb) for tb in DEFAULT_TABLES]
        self.roles = list(PRODUCTION_ROLES)
        self.employees = [dict(e) for e in DEFAULT_EMPLOYEES]
        self.attendance_punches = []
        self.kiosk_settings = {
            "admin_pin": "1234",
            "kiosk_name": "Borne Entrée Atelier",
            "qr_token": "kiosk_atelier_token"
        }
        self.face_credentials = {}
        self.save()

    def save(self):
        data = {
            "roles": self.roles,
            "joinery_types": self.joinery_types,
            "tables": self.tables,
            "employees": self.employees,
            "attendance_punches": self.attendance_punches,
            "kiosk_settings": self.kiosk_settings,
            "face_credentials": self.face_credentials
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --- Gestion des Types de Menuiseries ---
    def get_settings(self) -> Dict[str, Any]:
        enriched_types = []
        for t in self.joinery_types:
            t_copy = dict(t)
            total_time = float(t.get("temps_moyen_min", 60.0))
            ratios = t.get("ratios", {})
            
            total_pct = sum(float(v) for v in ratios.values()) if ratios else 0.0
            
            minutes_by_role = {}
            for r_id, pct in ratios.items():
                minutes_by_role[r_id] = round((total_time * float(pct)) / 100.0, 1)
                
            t_copy["total_pct"] = round(total_pct, 1)
            t_copy["is_valid_100"] = abs(total_pct - 100.0) < 0.1
            t_copy["minutes_by_role"] = minutes_by_role
            enriched_types.append(t_copy)
            
        return {
            "roles": self.roles,
            "joinery_types": enriched_types,
            "tables": self.tables,
            "employees": self.employees
        }

    def add_role_to_type(self, type_id: str, role_id: str, default_pct: float = 10.0) -> Dict[str, Any]:
        for t in self.joinery_types:
            if t["id"] == type_id:
                if "ratios" not in t or not isinstance(t["ratios"], dict):
                    t["ratios"] = {}
                t["ratios"][role_id] = float(default_pct)
                self.save()
                return t
        raise ValueError(f"Type introuvable: {type_id}")

    def remove_role_from_type(self, type_id: str, role_id: str) -> Dict[str, Any]:
        for t in self.joinery_types:
            if t["id"] == type_id:
                if "ratios" in t and role_id in t["ratios"]:
                    del t["ratios"][role_id]
                    self.save()
                return t
        raise ValueError(f"Type introuvable: {type_id}")

    def update_type(self, type_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        for t in self.joinery_types:
            if t["id"] == type_id:
                if "label" in updates:
                    t["label"] = updates["label"]
                if "temps_moyen_min" in updates:
                    t["temps_moyen_min"] = float(updates["temps_moyen_min"])
                if "ratios" in updates and isinstance(updates["ratios"], dict):
                    t["ratios"] = {k: float(v) for k, v in updates["ratios"].items()}
                if "description" in updates:
                    t["description"] = updates["description"]
                if "gamme" in updates:
                    t["gamme"] = updates["gamme"]
                if "categorie" in updates:
                    t["categorie"] = updates["categorie"]
                if "has_joint_vitrage" in updates:
                    t["has_joint_vitrage"] = bool(updates["has_joint_vitrage"])
                self.save()
                return t
        raise ValueError(f"Type introuvable: {type_id}")

    def add_type(self, type_data: Dict[str, Any]) -> Dict[str, Any]:
        type_id = type_data.get("id") or f"type_{len(self.joinery_types) + 1}"
        base_id = type_id
        c = 1
        while any(t["id"] == type_id for t in self.joinery_types):
            type_id = f"{base_id}_{c}"
            c += 1
            
        new_item = {
            "id": type_id,
            "label": type_data.get("label", "Nouveau type"),
            "gamme": type_data.get("gamme", "Gamme standard"),
            "categorie": type_data.get("categorie", "CAT-F - Ouvrant"),
            "has_joint_vitrage": type_data.get("has_joint_vitrage", True),
            "composants_count": int(type_data.get("composants_count", 15)),
            "description": type_data.get("description", "Menuiserie atelier"),
            "temps_moyen_min": float(type_data.get("temps_moyen_min", 60.0)),
            "ratios": type_data.get("ratios", {r["id"]: r.get("default_pct", 20) for r in self.roles})
        }
        self.joinery_types.append(new_item)
        self.save()
        return new_item

    def delete_type(self, type_id: str) -> bool:
        self.joinery_types = [t for t in self.joinery_types if t["id"] != type_id]
        self.save()
        return True

    def reset_to_defaults(self) -> List[Dict[str, Any]]:
        self.joinery_types = [dict(t) for t in CATALOG_JOINERY_TYPES]
        self.tables = [dict(tb) for tb in DEFAULT_TABLES]
        self.roles = list(PRODUCTION_ROLES)
        self.employees = [dict(e) for e in DEFAULT_EMPLOYEES]
        self.attendance_punches = []
        self.kiosk_settings = {
            "admin_pin": "1234",
            "kiosk_name": "Borne Entrée Atelier",
            "qr_token": "kiosk_atelier_token"
        }
        self.face_credentials = {}
        self.save()
        return self.joinery_types

    # --- Gestion des Employés d'Atelier ---
    def get_employees(self) -> List[Dict[str, Any]]:
        return self.employees

    def add_employee(self, emp_data: Dict[str, Any]) -> Dict[str, Any]:
        new_num = len(self.employees) + 1
        emp_id = emp_data.get("id") or f"emp_{new_num}"
        base_id = emp_id
        c = 1
        while any(e["id"] == emp_id for e in self.employees):
            emp_id = f"{base_id}_{c}"
            c += 1

        is_active = emp_data.get("active", True)
        now_time = datetime.now().strftime("%H:%M:%S")
        has_face = bool(emp_data.get("face_id_enrolled") or emp_data.get("face_photo"))

        new_emp = {
            "id": emp_id,
            "name": emp_data.get("name", f"Employé {new_num}").strip(),
            "code": emp_data.get("code", f"EMP-{new_num:02d}").strip(),
            "specialty": emp_data.get("specialty", "Opérateur de fabrication").strip(),
            "phone": emp_data.get("phone", "").strip(),
            "active": is_active,
            "presence_status": emp_data.get("presence_status", "PRESENT" if is_active else "ABSENT"),
            "last_punch_at": emp_data.get("last_punch_at", now_time if is_active else None),
            "face_id_enrolled": has_face
        }
        self.employees.append(new_emp)

        if emp_data.get("face_photo"):
            self.face_credentials[emp_id] = {
                "employee_id": emp_id,
                "photo_data_url": emp_data["face_photo"],
                "enrolled_at": datetime.now().isoformat(),
                "enrolled_by": emp_data.get("enrolled_by", "ADMIN")
            }

        self.save()
        return new_emp

    def update_employee(self, emp_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        for emp in self.employees:
            if emp["id"] == emp_id:
                for k, v in updates.items():
                    emp[k] = v
                self.save()
                return emp
        raise ValueError(f"Employé introuvable: {emp_id}")

    def delete_employee(self, emp_id: str) -> bool:
        if len(self.employees) <= 1:
            raise ValueError("Impossible de supprimer le dernier employé.")
        
        self.employees = [e for e in self.employees if e["id"] != emp_id]
        if emp_id in self.face_credentials:
            del self.face_credentials[emp_id]
        
        # Réassigner les tables qui utilisaient cet employé
        fallback_emp_id = self.employees[0]["id"]
        for tb in self.tables:
            for assignment in tb.get("role_assignments", []):
                if assignment.get("employee_id") == emp_id:
                    assignment["employee_id"] = fallback_emp_id
                    
        self.save()
        return True

    # --- Pointage & Système Biométrique Face ID ---
    def record_punch(self, emp_id: str, punch_type: str = "AUTO", method: str = "FACE_ID", confidence: float = 0.98, notes: str = "") -> Dict[str, Any]:
        emp = next((e for e in self.employees if e["id"] == emp_id), None)
        if not emp:
            raise ValueError(f"Employé {emp_id} introuvable")

        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        time_short = now.strftime("%H:%M:%S")

        current_status = emp.get("presence_status", "ABSENT")
        if punch_type == "AUTO":
            target_type = "OUT" if current_status == "PRESENT" else "IN"
        else:
            target_type = punch_type.upper()

        if target_type == "IN":
            emp["presence_status"] = "PRESENT"
            emp["active"] = True
        elif target_type == "OUT":
            emp["presence_status"] = "LEFT"
            emp["active"] = False
        elif target_type == "BREAK_START":
            emp["presence_status"] = "BREAK"
            emp["active"] = True
        elif target_type == "BREAK_END":
            emp["presence_status"] = "PRESENT"
            emp["active"] = True

        emp["last_punch_at"] = time_short

        punch_record = {
            "id": f"punch_{int(now.timestamp() * 1000)}",
            "employee_id": emp_id,
            "employee_name": emp["name"],
            "employee_code": emp.get("code", emp_id),
            "punch_type": target_type,
            "punch_time": timestamp_str,
            "time_short": time_short,
            "method": method,
            "confidence": round(confidence, 3),
            "notes": notes
        }
        self.attendance_punches.insert(0, punch_record)
        if len(self.attendance_punches) > 200:
            self.attendance_punches = self.attendance_punches[:200]
        self.save()
        return punch_record

    def save_face_credential(self, emp_id: str, photo_data_url: str, embedding: Optional[List[float]] = None) -> Dict[str, Any]:
        emp = next((e for e in self.employees if e["id"] == emp_id), None)
        if not emp:
            raise ValueError(f"Employé {emp_id} introuvable")
        
        emp["face_id_enrolled"] = True
        self.face_credentials[emp_id] = {
            "employee_id": emp_id,
            "photo_data_url": photo_data_url,
            "embedding": embedding or [0.1] * 128,
            "enrolled_at": datetime.now().isoformat(),
            "enrolled_by": "ADMIN"
        }
        self.save()
        return self.face_credentials[emp_id]

    def get_face_credential(self, emp_id: str) -> Optional[Dict[str, Any]]:
        return self.face_credentials.get(emp_id)

    def verify_admin_pin(self, pin: str) -> bool:
        configured_pin = self.kiosk_settings.get("admin_pin", "1234")
        return str(pin).strip() == str(configured_pin).strip()

    def set_admin_pin(self, new_pin: str):
        if not new_pin or len(new_pin.strip()) < 4:
            raise ValueError("Le code PIN doit comporter au moins 4 chiffres.")
        self.kiosk_settings["admin_pin"] = new_pin.strip()
        self.save()

    def generate_kiosk_qr(self, target_url: str) -> str:
        if qrcode is not None:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(target_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        else:
            import urllib.parse
            encoded = urllib.parse.quote(target_url)
            return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={encoded}"

    def get_recent_punches(self, limit: int = 25) -> List[Dict[str, Any]]:
        return self.attendance_punches[:limit]


    # --- Gestion des Tables d'Atelier & Affectations Multi-Rôles / Employés ---
    def get_tables(self) -> List[Dict[str, Any]]:
        return self.tables

    def get_roles(self) -> List[Dict[str, Any]]:
        return self.roles

    def add_role_to_table(self, table_id: str, role_id: str, employee_id: str) -> Dict[str, Any]:
        for tb in self.tables:
            if tb["id"] == table_id:
                if "role_assignments" not in tb or not isinstance(tb["role_assignments"], list):
                    tb["role_assignments"] = []
                
                # Vérifier si ce rôle est déjà présent sur la table
                for a in tb["role_assignments"]:
                    if a["role_id"] == role_id:
                        a["employee_id"] = employee_id
                        self.save()
                        return tb
                        
                tb["role_assignments"].append({
                    "role_id": role_id,
                    "employee_id": employee_id
                })
                self.save()
                return tb
        raise ValueError(f"Table introuvable: {table_id}")

    def remove_role_from_table(self, table_id: str, role_id: str) -> Dict[str, Any]:
        for tb in self.tables:
            if tb["id"] == table_id:
                assignments = tb.get("role_assignments", [])
                tb["role_assignments"] = [a for a in assignments if a.get("role_id") != role_id]
                self.save()
                return tb
        raise ValueError(f"Table introuvable: {table_id}")

    def update_table_role_employee(self, table_id: str, role_id: str, new_employee_id: str) -> Dict[str, Any]:
        for tb in self.tables:
            if tb["id"] == table_id:
                for a in tb.get("role_assignments", []):
                    if a.get("role_id") == role_id:
                        a["employee_id"] = new_employee_id
                        self.save()
                        return tb
        raise ValueError(f"Affectation rôle/table introuvable")

    def update_table(self, table_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        for tb in self.tables:
            if tb["id"] == table_id:
                for k, v in updates.items():
                    tb[k] = v
                self.save()
                return tb
        raise ValueError(f"Table introuvable: {table_id}")

    def add_table(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        new_num = len(self.tables) + 1
        t_id = table_data.get("id") or f"table_{new_num}"
        base_id = t_id
        c = 1
        while any(t["id"] == t_id for t in self.tables):
            t_id = f"{base_id}_{c}"
            c += 1

        fallback_emp = self.employees[0]["id"] if self.employees else "emp_1"
        fallback_role = self.roles[0]["id"] if self.roles else "coupe"
        
        assignments = table_data.get("role_assignments")
        if not assignments:
            assignments = [{"role_id": fallback_role, "employee_id": fallback_emp}]

        new_table = {
            "id": t_id,
            "name": table_data.get("name", f"Table {new_num}"),
            "code": table_data.get("code", f"T{new_num}"),
            "description": table_data.get("description", "Poste de travail atelier"),
            "active": table_data.get("active", True),
            "role_assignments": assignments
        }
        self.tables.append(new_table)
        self.save()
        return new_table

    def delete_table(self, table_id: str) -> bool:
        self.tables = [tb for tb in self.tables if tb["id"] != table_id]
        self.save()
        return True

    def set_table_count(self, target_count: int):
        target_count = max(1, min(24, int(target_count)))
        curr = len(self.tables)
        fallback_emp = self.employees[0]["id"] if self.employees else "emp_1"
        if target_count > curr:
            for i in range(curr + 1, target_count + 1):
                role_cycle = self.roles[(i - 1) % len(self.roles)]["id"]
                emp_cycle = self.employees[(i - 1) % len(self.employees)]["id"] if self.employees else fallback_emp
                self.tables.append({
                    "id": f"table_{i}",
                    "name": f"Table {i}",
                    "code": f"T{i}",
                    "description": f"Poste de fabrication Table {i}",
                    "active": True,
                    "role_assignments": [
                        {"role_id": role_cycle, "employee_id": emp_cycle}
                    ]
                })
        elif target_count < curr:
            self.tables = self.tables[:target_count]
        self.save()

    # --- Gestion des Rôles Atelier Personnalisés ---
    def add_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        label = role_data.get("label", "Nouveau Rôle").strip()
        base_id = role_data.get("id") or label.lower().replace(" ", "_").replace("/", "_")
        role_id = base_id
        c = 1
        while any(r["id"] == role_id for r in self.roles):
            role_id = f"{base_id}_{c}"
            c += 1

        new_role = {
            "id": role_id,
            "label": label,
            "color": role_data.get("color", "#64748B"),
            "default_pct": float(role_data.get("default_pct", 10)),
            "icon": role_data.get("icon", "precision_manufacturing")
        }
        self.roles.append(new_role)
        self.save()
        return new_role

    def update_role(self, role_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        for r in self.roles:
            if r["id"] == role_id:
                if "label" in updates:
                    r["label"] = updates["label"].strip()
                if "color" in updates:
                    r["color"] = updates["color"].strip()
                if "default_pct" in updates:
                    r["default_pct"] = float(updates["default_pct"])
                if "icon" in updates:
                    r["icon"] = updates["icon"].strip()
                self.save()
                return r
        raise ValueError(f"Rôle introuvable: {role_id}")

    def delete_role(self, role_id: str) -> bool:
        if len(self.roles) <= 1:
            raise ValueError("Impossible de supprimer le dernier rôle.")
        
        self.roles = [r for r in self.roles if r["id"] != role_id]
        
        # Nettoyer les affectations de ce rôle dans les tables
        for tb in self.tables:
            assignments = tb.get("role_assignments", [])
            tb["role_assignments"] = [a for a in assignments if a.get("role_id") != role_id]
            if not tb["role_assignments"] and self.roles and self.employees:
                tb["role_assignments"].append({"role_id": self.roles[0]["id"], "employee_id": self.employees[0]["id"]})
                
        self.save()
        return True

settings_mgr = SettingsManager()

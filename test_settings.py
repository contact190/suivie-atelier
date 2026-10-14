"""
Tests Unitaires : Catalogue (32 Modèles), Rôles Personnalisables, Tables & Attribution Libre par Modèle
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from settings_manager import settings_mgr

def test_all():
    print("=" * 65)
    print("🧪 Test : Modèles, Rôles & Attribution Libre des Rôles par Modèle")
    print("=" * 65)

    # 1. Vérification des 32 modèles du catalogue
    settings = settings_mgr.get_settings()
    types = settings["joinery_types"]
    assert len(types) == 32, f"Attendu 32 modèles, obtenu {len(types)}"
    print(f"✅ Exactement 32 modèles du catalogue chargés.")

    # 2. Vérification des rôles d'atelier
    initial_roles = settings_mgr.get_roles()
    assert len(initial_roles) >= 5, f"Attendu au moins 5 rôles, obtenu {len(initial_roles)}"
    print(f"✅ {len(initial_roles)} rôles d'atelier chargés.")

    # 3. Création d'un rôle personnalisé
    new_role = settings_mgr.add_role({
        "label": "Soudure & Équerres",
        "color": "#EC4899",
        "default_pct": 10.0
    })
    print(f"✅ Création d'un rôle personnalisé '{new_role['label']}' validée.")

    # 4. Ajout de ce rôle à un modèle de menuiserie spécifique (ex: H31 2 Ouvrant SV)
    model_id = "h31_2ouv_sv"
    settings_mgr.add_role_to_type(model_id, new_role["id"], default_pct=10.0)
    
    # Vérification que le modèle contient le nouveau rôle
    h31 = next(t for t in settings_mgr.get_settings()["joinery_types"] if t["id"] == model_id)
    assert new_role["id"] in h31["ratios"]
    print(f"✅ Rôle '{new_role['label']}' ajouté avec succès au modèle '{h31['label']}'.")

    # 5. Retrait d'un rôle d'un modèle (ex: retirer 'vitrage' du modèle)
    settings_mgr.remove_role_from_type(model_id, "vitrage")
    h31_after = next(t for t in settings_mgr.get_settings()["joinery_types"] if t["id"] == model_id)
    assert "vitrage" not in h31_after["ratios"]
    print(f"✅ Rôle 'vitrage' retiré avec succès du modèle '{h31_after['label']}'.")

    # 6. Test de la gestion des employés d'atelier
    employees = settings_mgr.get_employees()
    assert len(employees) >= 6, f"Attendu au moins 6 employés, obtenu {len(employees)}"
    print(f"✅ {len(employees)} employés d'atelier chargés (Karim, Moussa, Thomas, Lucas, Youssef, Sofiane).")

    new_emp = settings_mgr.add_employee({
        "name": "Nabil Testeur",
        "code": "EMP-99",
        "specialty": "Polyvalent Usinage & Débit",
        "phone": "06 99 88 77 66",
        "active": True
    })
    assert any(e["id"] == new_emp["id"] for e in settings_mgr.get_employees())
    print(f"✅ Création d'un employé '{new_emp['name']}' ({new_emp['code']}) validée.")

    # 7. Test des tables multi-rôles avec affectation d'employés
    tables = settings_mgr.get_tables()
    assert len(tables) >= 6, f"Attendu au moins 6 tables, obtenu {len(tables)}"
    t1 = tables[0]
    
    # Ajouter un deuxième rôle à la Table 1 (ex: 'grugage') avec Nabil
    settings_mgr.add_role_to_table(t1["id"], "grugage", new_emp["id"])
    t1_updated = next(t for t in settings_mgr.get_tables() if t["id"] == t1["id"])
    roles_on_t1 = [a["role_id"] for a in t1_updated["role_assignments"]]
    assert "coupe" in roles_on_t1 and "grugage" in roles_on_t1
    print(f"✅ Table '{t1['name']}' configurée avec succès en MULTI-RÔLES ({', '.join(roles_on_t1)}).")

    # Vérifier que le rôle 'grugage' est bien assigné à Nabil
    grugage_assign = next(a for a in t1_updated["role_assignments"] if a["role_id"] == "grugage")
    assert grugage_assign["employee_id"] == new_emp["id"]
    print(f"✅ Rôle 'grugage' sur '{t1['name']}' correctement assigné à l'employé '{new_emp['name']}'.")

    # Mettre à jour l'employé pour le rôle coupe sur la table 1
    settings_mgr.update_table_role_employee(t1["id"], "coupe", new_emp["id"])
    t1_updated2 = next(t for t in settings_mgr.get_tables() if t["id"] == t1["id"])
    coupe_assign = next(a for a in t1_updated2["role_assignments"] if a["role_id"] == "coupe")
    assert coupe_assign["employee_id"] == new_emp["id"]
    print(f"✅ Réaffectation d'employé sur le rôle 'coupe' de '{t1['name']}' validée.")

    # Retirer le rôle grugage de la table 1
    settings_mgr.remove_role_from_table(t1["id"], "grugage")
    t1_updated3 = next(t for t in settings_mgr.get_tables() if t["id"] == t1["id"])
    roles_on_t1_after = [a["role_id"] for a in t1_updated3["role_assignments"]]
    assert "grugage" not in roles_on_t1_after
    print(f"✅ Rôle 'grugage' retiré avec succès de '{t1['name']}'.")

    # 8. Test suppression d'un employé avec réaffectation automatique
    settings_mgr.delete_employee(new_emp["id"])
    assert not any(e["id"] == new_emp["id"] for e in settings_mgr.get_employees())
    # Vérifier que la table 1 n'a plus new_emp mais un fallback
    t1_fallback = next(t for t in settings_mgr.get_tables() if t["id"] == t1["id"])
    assert t1_fallback["role_assignments"][0]["employee_id"] != new_emp["id"]
    print(f"✅ Suppression d'employé avec réassignation de secours validée.")

    # 9. Test du Système de Pointage & Face ID
    punch_in = settings_mgr.record_punch("emp_1", punch_type="IN", method="FACE_ID", confidence=0.97)
    assert punch_in["punch_type"] == "IN"
    emp_1 = next(e for e in settings_mgr.get_employees() if e["id"] == "emp_1")
    assert emp_1["presence_status"] == "PRESENT"
    print(f"✅ Pointage ENTRÉE Face ID enregistré pour {emp_1['name']} à {punch_in['time_short']}.")

    # Enregistrement Face ID avec vraies images test
    from PIL import Image, ImageDraw
    import io, base64

    # Photo Référence : Employé 1
    im_ref = Image.new('RGB', (160, 160), color=(240, 200, 180))
    d_ref = ImageDraw.Draw(im_ref)
    d_ref.ellipse([50, 40, 70, 60], fill=(30, 30, 30))
    d_ref.ellipse([90, 40, 110, 60], fill=(30, 30, 30))
    d_ref.rectangle([60, 110, 100, 125], fill=(180, 50, 50))
    buf_ref = io.BytesIO()
    im_ref.save(buf_ref, format='JPEG')
    b64_ref = "data:image/jpeg;base64," + base64.b64encode(buf_ref.getvalue()).decode()

    face_cred = settings_mgr.save_face_credential("emp_1", photo_data_url=b64_ref)
    assert face_cred["employee_id"] == "emp_1"
    assert emp_1["face_id_enrolled"] is True
    print(f"✅ Enrôlement Face ID validé pour {emp_1['name']}.")

    # Photo B : Personne DIFFÉRENTE devant la caméra
    im_diff = Image.new('RGB', (160, 160), color=(100, 70, 50))
    d_diff = ImageDraw.Draw(im_diff)
    d_diff.ellipse([30, 60, 60, 90], fill=(10, 10, 10))
    d_diff.ellipse([100, 60, 130, 90], fill=(10, 10, 10))
    d_diff.rectangle([70, 130, 110, 145], fill=(220, 80, 80))
    buf_diff = io.BytesIO()
    im_diff.save(buf_diff, format='JPEG')
    b64_diff = "data:image/jpeg;base64," + base64.b64encode(buf_diff.getvalue()).decode()

    res_diff = settings_mgr.verify_face_match("emp_1", b64_diff, threshold=65.0)
    assert res_diff["match"] is False
    print(f"✅ Rejet formel du mauvais visage validé (Score: {res_diff['score']}% < 65%).")

    # Photo A' : MÊME PERSONNE avec légère variation
    im_same = Image.new('RGB', (160, 160), color=(236, 198, 178))
    d_same = ImageDraw.Draw(im_same)
    d_same.ellipse([51, 41, 71, 61], fill=(32, 32, 32))
    d_same.ellipse([91, 41, 111, 61], fill=(32, 32, 32))
    d_same.rectangle([61, 111, 101, 126], fill=(182, 52, 52))
    buf_same = io.BytesIO()
    im_same.save(buf_same, format='JPEG')
    b64_same = "data:image/jpeg;base64," + base64.b64encode(buf_same.getvalue()).decode()

    res_same = settings_mgr.verify_face_match("emp_1", b64_same, threshold=65.0)
    assert res_same["match"] is True
    print(f"✅ Acceptation du bon visage validée (Score: {res_same['score']}% >= 65%).")

    # Test vérification code PIN Admin
    assert settings_mgr.verify_admin_pin("1234") is True
    assert settings_mgr.verify_admin_pin("9999") is False
    print(f"✅ Sécurité Admin PIN de la borne validée.")

    # Test génération QR Code
    qr_b64 = settings_mgr.generate_kiosk_qr("http://localhost:8000/pointage")
    assert "data:image/png;base64," in qr_b64 or "qrserver" in qr_b64
    print(f"✅ Génération du QR Code borne de pointage validée.")

    # 10. Rétablissement des réglages par défaut
    settings_mgr.reset_to_defaults()
    h31_default = next(t for t in settings_mgr.get_settings()["joinery_types"] if t["id"] == model_id)
    assert "vitrage" in h31_default["ratios"]
    print(f"✅ Rétablissement complet des réglages par défaut validé.")

    print("\n" + "=" * 65)
    print("🏆 TOUS LES TESTS (MODÈLES, RÔLES, TABLES, EMPLOYÉS & FACE ID) SONT RÉUSSIS !")
    print("=" * 65)

if __name__ == "__main__":
    test_all()



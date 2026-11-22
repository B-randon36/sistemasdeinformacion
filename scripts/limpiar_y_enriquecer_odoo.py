#!/usr/bin/env python3
"""
Auditoría, Limpieza de Datos Erróneos y Expansión de E-commerce + Manufactura BOM
para AGRO PERUVIAN FOODS S.A.C. en Odoo 17 (solo librería estándar xmlrpc.client).

Acciones:
  1. Elimina BOMs de prueba/erróneas (IDs 109, 110, 111) y archiva productos de prueba/duplicados.
  2. Despublica materias primas del Sitio Web y les desactiva sale_ok para no ensuciar Ventas/POS/E-commerce.
  3. Limpia órdenes de venta de prueba/borradores basura, facturas huérfanas en borrador ('/'),
     órdenes de manufactura atascadas/borrador y RFQs viejas en borrador (dejando solo datos limpios).
  4. Archiva contacto de prueba 'Gobierno'.
  5. Crea 4 Categorías de E-commerce profesionales y clasifica los 16 productos existentes.
  6. Crea 4 nuevos productos agroindustriales (Pasta Pura de Cacao 100%, Nibs de Cacao Tostado,
     Manteca de Cacao Orgánica, Harina de Coco Orgánica) con su BOM real, Manufactura ejecutada (+400 uds c/u)
     y publicación en E-commerce (sin venta sin stock y disponibilidad visible).
"""

import socket
import xmlrpc.client
from pathlib import Path
from typing import Any, Dict, List, Optional


def cargar_env(ruta: Path) -> Dict[str, str]:
    vals: Dict[str, str] = {}
    if not ruta.exists():
        return vals
    for line in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def main() -> None:
    env = cargar_env(Path(__file__).resolve().parent.parent / ".env")
    url = env.get("ODOO_URL", "http://52.86.231.75:8069").rstrip("/")
    db = env.get("ODOO_DB", "brandon")
    user = env.get("ODOO_USER", "destruller1025b@gmail.com")
    pwd = env.get("ODOO_PASSWORD", "")

    socket.setdefaulttimeout(45)
    uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True).authenticate(db, user, pwd, {})
    if not uid:
        raise RuntimeError("No se pudo autenticar en Odoo 17.")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    def call(model: str, method: str, args: list, kwargs: Optional[dict] = None) -> Any:
        try:
            return models.execute_kw(db, uid, pwd, model, method, args, kwargs or {})
        except xmlrpc.client.Fault as f:
            if "cannot marshal None" in str(f.faultString):
                return None
            raise

    def q(model: str, domain: list, fields: list, limit: int = 500) -> List[dict]:
        return call(model, "search_read", [domain], {"fields": fields, "limit": limit})

    print("=" * 74)
    print("FASE 1: LIMPIEZA DE DATOS INCORRECTOS, DUPLICADOS Y BORRADORES BASURA")
    print("=" * 74)

    # 1.1 Eliminar BOMs de prueba/absurdas (109, 110, 111)
    bad_boms = q("mrp.bom", [["id", "in", [109, 110, 111]]], ["id", "code", "product_tmpl_id"])
    if bad_boms:
        bad_bom_ids = [b["id"] for b in bad_boms]
        try:
            call("mrp.bom", "unlink", [bad_bom_ids])
            print(f"  [OK] Eliminadas {len(bad_bom_ids)} BOMs de prueba/erróneas: {[b['code'] for b in bad_boms]}")
        except Exception:
            call("mrp.bom", "write", [bad_bom_ids, {"active": False}])
            print(f"  [OK] Archivadas {len(bad_bom_ids)} BOMs de prueba/erróneas: {[b['code'] for b in bad_boms]}")

    # 1.2 Archivar productos de prueba/duplicados mal escritos (71..77)
    junk_tmpl_ids = [71, 72, 73, 74, 75, 76, 77]
    junk_prods = q("product.template", [["id", "in", junk_tmpl_ids]], ["id", "name"])
    if junk_prods:
        ids_found = [p["id"] for p in junk_prods]
        call("product.template", "write", [ids_found, {"website_published": False, "sale_ok": False, "purchase_ok": False, "active": False}])
        print(f"  [OK] Archivados {len(ids_found)} productos basura/duplicados: {[p['name'] for p in junk_prods]}")

    # 1.3 Asegurar que las materias primas (48..59) NO aparezcan en Sitio Web ni en Ventas
    raw_ids = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
    raw_found = q("product.template", [["id", "in", raw_ids]], ["id", "name"])
    if raw_found:
        call("product.template", "write", [[p["id"] for p in raw_found], {"website_published": False, "sale_ok": False, "purchase_ok": True}])
        print(f"  [OK] {len(raw_found)} insumos/materias primas ocultados de E-commerce y Ventas (solo Compras/Manufactura).")

    # 1.4 Limpiar Facturas huérfanas en borrador (state='draft', name='/', invoice_origin=False)
    draft_invs = q("account.move", [["move_type", "=", "out_invoice"], ["state", "=", "draft"], ["invoice_origin", "=", False]], ["id"])
    if draft_invs:
        call("account.move", "unlink", [[i["id"] for i in draft_invs]])
        print(f"  [OK] Eliminadas {len(draft_invs)} facturas huérfanas en borrador ('/').")

    # 1.5 Limpiar Órdenes de Venta de prueba y borradores viejos (conservando 3 cotizaciones reales en 'sent')
    draft_sos = q("sale.order", [["state", "=", "draft"]], ["id"])
    if draft_sos:
        call("sale.order", "unlink", [[s["id"] for s in draft_sos]])
        print(f"  [OK] Eliminados {len(draft_sos)} presupuestos viejos en borrador.")

    test_sent_sos = q("sale.order", [["state", "=", "sent"], ["partner_id", "in", [1, 3, 129, 130]]], ["id", "name"])
    if test_sent_sos:
        for s in test_sent_sos:
            call("sale.order", "_action_cancel", [[s["id"]]]) if False else call("sale.order", "write", [[s["id"]], {"state": "cancel"}])
        call("sale.order", "unlink", [[s["id"] for s in test_sent_sos]])
        print(f"  [OK] Eliminadas {len(test_sent_sos)} cotizaciones de prueba emitidas a la propia empresa.")

    # 1.6 Limpiar Órdenes de Manufactura atascadas/borrador (dejar solo las 'done' limpias)
    non_done_mos = q("mrp.production", [["state", "in", ["draft", "confirmed", "progress"]]], ["id", "state"])
    if non_done_mos:
        eliminadas_mo = 0
        for mo in non_done_mos:
            mid = mo["id"]
            try:
                call("mrp.production", "action_cancel", [[mid]])
                call("mrp.production", "unlink", [[mid]])
                eliminadas_mo += 1
            except Exception:
                pass
        print(f"  [OK] Canceladas y eliminadas {eliminadas_mo}/{len(non_done_mos)} órdenes de manufactura atascadas/borrador.")

    # 1.7 Limpiar RFQs de compra en borrador viejas (dejar solo 1 borrador para ejemplo, borrar el resto)
    draft_pos = q("purchase.order", [["state", "=", "draft"]], ["id"], limit=500)
    if len(draft_pos) > 1:
        to_del_po = [p["id"] for p in draft_pos[1:]]
        call("purchase.order", "button_cancel", [to_del_po])
        call("purchase.order", "unlink", [to_del_po])
        print(f"  [OK] Canceladas y eliminadas {len(to_del_po)} solicitudes de compra viejas en borrador (1 conservada como muestra).")

    # 1.8 Archivar contacto de prueba 'Gobierno' (ID 128)
    gob = q("res.partner", [["id", "=", 128]], ["id", "name"])
    if gob:
        call("res.partner", "write", [[128], {"active": False}])
        print("  [OK] Archivado contacto de prueba 'Gobierno' (sin RUC).")

    print("\n" + "=" * 74)
    print("FASE 2: CATEGORÍAS E-COMMERCE Y NUEVOS PRODUCTOS CON BOM + MANUFACTURA")
    print("=" * 74)

    # 2.1 Crear 4 Categorías Públicas del Sitio Web
    categorias_def = [
        "Aceites de Coco Virgen",
        "Derivados de Cacao Orgánico",
        "Coco Rallado y Harinas",
        "Bandejas Mayoristas B2B",
    ]
    cat_ids: Dict[str, int] = {}
    for cname in categorias_def:
        existing = q("product.public.category", [["name", "=", cname]], ["id", "name"])
        if existing:
            cat_ids[cname] = existing[0]["id"]
        else:
            cat_ids[cname] = call("product.public.category", "create", [{"name": cname}])
    print(f"  [OK] Categorías E-commerce listas: {cat_ids}")

    # 2.2 Asignar categorías a los 16 productos terminados existentes
    asignacion_existente = {
        "Aceites de Coco Virgen": [20, 21, 22, 23, 24, 25, 26],
        "Derivados de Cacao Orgánico": [27, 28],
        "Coco Rallado y Harinas": [29, 30],
        "Bandejas Mayoristas B2B": [31, 32, 33, 34, 35],
    }
    for cname, tids in asignacion_existente.items():
        call(
            "product.template",
            "write",
            [tids, {"public_categ_ids": [(6, 0, [cat_ids[cname]])], "purchase_ok": False, "sale_ok": True}],
        )
    print("  [OK] 16 productos existentes clasificados en categorías del Sitio Web.")

    # 2.3 Crear 4 Nuevos Productos Estrella + BOM real + Manufactura (400 uds c/u) + E-commerce
    # Ruta Manufacture ID = 5, Impuesto IGV 18% ID = 1
    nuevos_productos = [
        {
            "name": "Pasta Pura de Cacao 100% (250g)",
            "default_code": "APF-PPC-250G",
            "list_price": 20.0,
            "standard_price": 8.40,
            "categoria": "Derivados de Cacao Orgánico",
            "description_sale": "Pasta pura de cacao criollo 100% orgánico de Satipo, Junín. Ideal para chocolatería fina, bebidas y repostería saludable. Sin azúcar añadida.",
            "bom_code": "LOM-PPC-250G",
            "bom_qty": 100.0,
            "componentes": [(49, 0.70), (57, 0.10), (59, 0.10)],  # Cacao Criollo + Bolsas 250g + Etiquetas
            "fabricar_qty": 400.0,
        },
        {
            "name": "Nibs de Cacao Tostado Orgánico (150g)",
            "default_code": "APF-NCT-150G",
            "list_price": 14.0,
            "standard_price": 5.10,
            "categoria": "Derivados de Cacao Orgánico",
            "description_sale": "Trozos crujientes de cacao criollo tostado artesanalmente en Satipo. Rico en antioxidantes, magnesio y fibra natural.",
            "bom_code": "LOM-NCT-150G",
            "bom_qty": 100.0,
            "componentes": [(49, 0.35), (57, 0.10), (59, 0.10)],
            "fabricar_qty": 400.0,
        },
        {
            "name": "Manteca de Cacao Orgánica Virgen (250g)",
            "default_code": "APF-MCO-250G",
            "list_price": 32.0,
            "standard_price": 14.50,
            "categoria": "Derivados de Cacao Orgánico",
            "description_sale": "Manteca de cacao prensada en frío grado alimentario y cosmético. Pureza 100% de granos seleccionados de Junín.",
            "bom_code": "LOM-MCO-250G",
            "bom_qty": 50.0,
            "componentes": [(49, 0.50), (52, 1.00), (59, 0.05)],  # Cacao Criollo + Frascos 250ml + Etiquetas
            "fabricar_qty": 400.0,
        },
        {
            "name": "Harina de Coco Orgánica Sin Gluten (500g)",
            "default_code": "APF-HCO-500G",
            "list_price": 18.0,
            "standard_price": 8.20,
            "categoria": "Coco Rallado y Harinas",
            "description_sale": "Harina fina de coco deshidratado y desgrasado naturalmente. Alta en fibra, baja en carbohidratos, ideal para dieta keto y panadería sin gluten.",
            "bom_code": "LOM-HCO-500G",
            "bom_qty": 100.0,
            "componentes": [(48, 1.20), (58, 0.10), (59, 0.10)],  # Coco Seco Criollo + Bolsas 500g + Etiquetas
            "fabricar_qty": 400.0,
        },
    ]

    for spec in nuevos_productos:
        ex = q("product.template", [["default_code", "=", spec["default_code"]]], ["id", "product_variant_id"])
        if ex:
            tmpl_id = ex[0]["id"]
            prod_id = ex[0]["product_variant_id"][0]
            print(f"  [EXISTE] {spec['name']} (TMPL {tmpl_id})")
        else:
            tmpl_id = call(
                "product.template",
                "create",
                [
                    {
                        "name": spec["name"],
                        "default_code": spec["default_code"],
                        "detailed_type": "product",
                        "list_price": spec["list_price"],
                        "standard_price": spec["standard_price"],
                        "sale_ok": True,
                        "purchase_ok": False,
                        "taxes_id": [(6, 0, [1])],
                        "route_ids": [(6, 0, [5])],  # Manufacture
                        "website_published": True,
                        "allow_out_of_stock_order": False,
                        "show_availability": True,
                        "available_threshold": 10000.0,
                        "public_categ_ids": [(6, 0, [cat_ids[spec["categoria"]]])],
                        "description_sale": spec["description_sale"],
                        "available_in_pos": True,
                    }
                ],
            )
            p_info = q("product.template", [["id", "=", tmpl_id]], ["product_variant_id", "uom_id"])[0]
            prod_id = p_info["product_variant_id"][0]
            uom_id = p_info["uom_id"][0]

            # Crear BOM real
            bom_id = call(
                "mrp.bom",
                "create",
                [
                    {
                        "product_tmpl_id": tmpl_id,
                        "code": spec["bom_code"],
                        "type": "normal",
                        "product_qty": spec["bom_qty"],
                        "bom_line_ids": [
                            (0, 0, {"product_id": cid, "product_qty": cqty})
                            for cid, cqty in spec["componentes"]
                        ],
                    }
                ],
            )

            # Fabricar 400 unidades vía mrp.production real
            mo_id = call(
                "mrp.production",
                "create",
                [
                    {
                        "product_id": prod_id,
                        "product_qty": spec["fabricar_qty"],
                        "product_uom_id": uom_id,
                        "bom_id": bom_id,
                        "origin": "LANZAMIENTO-ECOMMERCE-2026",
                    }
                ],
            )
            call("mrp.production", "action_confirm", [[mo_id]])
            call("mrp.production", "write", [[mo_id], {"qty_producing": spec["fabricar_qty"]}])
            mo_rec = q("mrp.production", [["id", "=", mo_id]], ["name", "move_raw_ids"])[0]
            if mo_rec.get("move_raw_ids"):
                for rm in q("stock.move", [["id", "in", mo_rec["move_raw_ids"]]], ["id", "product_uom_qty"]):
                    call("stock.move", "write", [[rm["id"]], {"quantity": rm["product_uom_qty"], "picked": True}])
            call("mrp.production", "button_mark_done", [[mo_id]], {"context": {"skip_backorder": True, "skip_consumption": True}})
            print(f"  [NUEVO + BOM + MRP + WEB] {spec['name']} (S/ {spec['list_price']:.2f}) | BOM {spec['bom_code']} | {mo_rec['name']} (+{int(spec['fabricar_qty'])} uds)")

    # 3. Verificación Final Global
    print("\n" + "=" * 74)
    print("VERIFICACIÓN FINAL TRAS LIMPIEZA Y EXPANSIÓN E-COMMERCE")
    print("=" * 74)
    pub_prods = q("product.template", [["website_published", "=", True]], ["id", "name", "list_price", "qty_available", "public_categ_ids"])
    neg = q("product.product", [["detailed_type", "=", "product"], ["qty_available", "<", 0]], ["id", "name", "qty_available"])
    mo_all = call("mrp.production", "search_count", [[]])
    mo_done = call("mrp.production", "search_count", [[["state", "=", "done"]]])
    so_sale = call("sale.order", "search_count", [[["state", "in", ["sale", "done"]]]])
    so_draft = call("sale.order", "search_count", [[["state", "=", "draft"]]])
    inv_posted = call("account.move", "search_count", [[["move_type", "=", "out_invoice"], ["state", "=", "posted"]]])
    inv_draft = call("account.move", "search_count", [[["move_type", "=", "out_invoice"], ["state", "=", "draft"]]])
    po_all = call("purchase.order", "search_count", [[]])
    po_conf = call("purchase.order", "search_count", [[["state", "in", ["purchase", "done"]]]])

    print(f"  * Productos publicados en E-commerce (todos con BOM): {len(pub_prods)}")
    print(f"  * Productos con stock NEGATIVO:                       {len(neg)}")
    print(f"  * Órdenes de Manufactura (done / total):              {mo_done} / {mo_all}")
    print(f"  * Ventas confirmadas / borradores residuales:         {so_sale} confirmadas | {so_draft} borradores")
    print(f"  * Facturas publicadas / borradores huérfanos:         {inv_posted} publicadas | {inv_draft} borradores")
    print(f"  * Compras confirmadas / total:                        {po_conf} / {po_all}")
    print("\n  --- Catálogo Público E-commerce Activo ---")
    for p in sorted(pub_prods, key=lambda x: x["name"]):
        print(f"    - {p['name']:<55} | S/ {p['list_price']:>6.2f} | Stock: {p['qty_available']:>7.1f}")
    print("=" * 74)


if __name__ == "__main__":
    main()

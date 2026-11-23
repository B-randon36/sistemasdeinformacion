#!/usr/bin/env python3
"""
Normaliza el inventario de Odoo 17 a cantidades realistas de una MYPE agroindustrial
(Agro Peruvian Foods S.A.C.) y corrige datos erróneos en productos:
- Elimina stocks exagerados (~5,000 cajas/sacos/millares) y decimales raros
- Corrige precios de venta en materias primas (Coco Seco S/ 5.00 -> S/ 0.00, sale_ok=False)
- Archiva productos basura de POS (Propinas [TIPS], Descuento [DISC] si no bloquean POS)
- Ajusta las reglas de reabastecimiento (stock mínimo / máximo) a escalas reales
"""

from pathlib import Path
import socket
import xmlrpc.client


def cargar_env(ruta: Path) -> dict:
    vals = {}
    if not ruta.exists():
        return vals
    for line in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def call(m, db, uid, pwd, model, method, args, kwargs=None):
    try:
        return m.execute_kw(db, uid, pwd, model, method, args, kwargs or {})
    except xmlrpc.client.Fault as e:
        if "cannot marshal None" in str(e):
            return None
        raise


def main():
    env = cargar_env(Path(__file__).resolve().parent.parent / ".env")
    url = env.get("ODOO_URL", "http://52.86.231.75:8069").rstrip("/")
    db = env.get("ODOO_DB", "brandon")
    user = env.get("ODOO_USER", "destruller1025b@gmail.com")
    pwd = env.get("ODOO_PASSWORD", "")

    socket.setdefaulttimeout(45)
    uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True).authenticate(db, user, pwd, {})
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    print(f"Conectado a Odoo ({url}) UID={uid}")

    # 1. Ubicación principal de stock (WH/Stock)
    wh = call(m, db, uid, pwd, "stock.warehouse", "search_read", [[["id", "=", 1]]], {"fields": ["lot_stock_id"]})
    stock_loc_id = wh[0]["lot_stock_id"][0]
    print(f"Ubicación de stock principal: ID={stock_loc_id}")

    # 2. Cantidades realistas por product.product ID
    target_qty = {
        # Productos Terminados
        20: 285.0,  # Aceite de Coco Virgen 30 ml
        21: 210.0,  # Aceite de Coco Virgen 120 ml
        22: 320.0,  # Aceite de Coco Virgen 250 ml
        23: 195.0,  # Aceite de Coco Virgen 460 ml
        24: 145.0,  # Aceite de Coco Virgen 1 L
        25: 68.0,   # Aceite de Coco Virgen | Balde 4 L
        26: 24.0,   # Aceite de Coco Virgen | Balde 20 L
        31: 38.0,   # Aceite 30ml | Bandeja Mayorista (x24)
        32: 26.0,   # Aceite 120ml | Bandeja Mayorista (x24)
        33: 42.0,   # Aceite 250ml | Bandeja Mayorista (x12)
        34: 31.0,   # Aceite 460ml | Bandeja Mayorista (x12)
        35: 28.0,   # Aceite 1L | Bandeja Mayorista (x6)
        27: 265.0,  # Cacao Grano Entero Sin Tostar 500g
        28: 158.0,  # Cacao Grano Entero Sin Tostar 1 kg
        29: 290.0,  # Coco Rallado Doypack 250g
        30: 184.0,  # Coco Rallado Doypack 500g
        68: 165.0,  # Pasta Pura de Cacao 100% (250g)
        69: 215.0,  # Nibs de Cacao Tostado Orgánico (150g)
        70: 132.0,  # Manteca de Cacao Orgánica Virgen (250g)
        71: 248.0,  # Harina de Coco Orgánica Sin Gluten (500g)
        # Materias Primas y Envases (unidades enteras realistas)
        48: 185.0,  # Coco Seco Criollo de Selva (Saco 50 kg)
        49: 92.0,   # Cacao Criollo en Baba / Grano Fermentado (Saco 50 kg)
        50: 35.0,   # Frascos de Vidrio 30ml (Caja x 100)
        51: 32.0,   # Frascos de Vidrio 120ml (Caja x 100)
        52: 48.0,   # Frascos de Vidrio 250ml (Caja x 50)
        53: 36.0,   # Frascos de Vidrio 460ml (Caja x 50)
        54: 28.0,   # Frascos de Vidrio 1L (Caja x 25)
        55: 18.0,   # Baldes Plásticos 4L (Pack x 20)
        56: 14.0,   # Baldes Plásticos 20L (Pack x 10)
        57: 12.0,   # Bolsas Doypack Kraft 250g (Millar)
        58: 9.0,    # Bolsas Doypack Kraft 500g (Millar)
        59: 24.0,   # Etiquetas Adhesivas Coco Tropical (Rollo x 1000)
    }

    # Verificar si alguno es kit (phantom BOM) para no tocarlo
    kit_boms = call(m, db, uid, pwd, "mrp.bom", "search_read", [[["type", "=", "phantom"]]], {"fields": ["product_tmpl_id"]})
    kit_tmpl_ids = {b["product_tmpl_id"][0] for b in kit_boms if b.get("product_tmpl_id")}

    adjusted = 0
    for pid, new_qty in target_qty.items():
        pinfo = call(m, db, uid, pwd, "product.product", "read", [[pid], ["name", "product_tmpl_id", "qty_available"]])
        if not pinfo:
            continue
        pinfo = pinfo[0]
        if pinfo["product_tmpl_id"][0] in kit_tmpl_ids:
            print(f"  [SKIP KIT] {pinfo['name']}")
            continue

        # Buscar quants en ubicaciones internas
        quants = call(
            m, db, uid, pwd, "stock.quant", "search_read",
            [[["product_id", "=", pid], ["location_id", "=", stock_loc_id]]],
            {"fields": ["id", "quantity"]}
        )
        if quants:
            qid = quants[0]["id"]
            call(m, db, uid, pwd, "stock.quant", "write", [[qid], {"inventory_quantity": new_qty}])
            call(m, db, uid, pwd, "stock.quant", "action_apply_inventory", [[qid]])
        else:
            qid = call(
                m, db, uid, pwd, "stock.quant", "create",
                [{"product_id": pid, "location_id": stock_loc_id, "inventory_quantity": new_qty}]
            )
            call(m, db, uid, pwd, "stock.quant", "action_apply_inventory", [[qid]])
        adjusted += 1

    print(f"[OK] Stock normalizado en {adjusted} productos a cantidades realistas.")

    # 3. Corregir materias primas (sale_ok=False, list_price=0.0, website_published=False)
    raw_prod_ids = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
    raw_prods = call(m, db, uid, pwd, "product.product", "read", [raw_prod_ids, ["product_tmpl_id"]])
    raw_tmpl_ids = [p["product_tmpl_id"][0] for p in raw_prods]
    call(m, db, uid, pwd, "product.template", "write", [raw_tmpl_ids, {
        "sale_ok": False,
        "purchase_ok": True,
        "list_price": 0.0,
        "is_published": False,
    }])
    print(f"[OK] Corregidas {len(raw_tmpl_ids)} materias primas (Precio venta S/ 0.00, No vendible en tienda).")

    # 4. Archivar Propinas [TIPS] y Descuento [DISC] para que no ensucien el catálogo de Inventario
    junk_tmpls = call(
        m, db, uid, pwd, "product.template", "search",
        [[["default_code", "in", ["TIPS", "DISC"]]]]
    )
    if junk_tmpls:
        try:
            call(m, db, uid, pwd, "product.template", "write", [junk_tmpls, {"active": False}])
            print(f"[OK] Archivados productos de sistema POS (TIPS / DISC): IDs {junk_tmpls}.")
        except Exception as e:
            print(f"[WARN] No se pudieron archivar TIPS/DISC (vinculados a POS): {e}")

    # 5. Actualizar Reglas de Reabastecimiento a escalas coherentes con el stock real
    new_rules = {
        48: (50.0,  250.0, 10.0),  # Coco Seco Criollo (stock 185)
        49: (30.0,  150.0, 5.0),   # Cacao Criollo (stock 92)
        52: (15.0,  60.0,  5.0),   # Frascos 250ml (stock 48)
        53: (12.0,  50.0,  5.0),   # Frascos 460ml (stock 36)
        59: (8.0,   35.0,  2.0),   # Etiquetas Coco Tropical (stock 24)
        22: (80.0,  400.0, 20.0),  # Aceite 250 ml (stock 320)
        23: (60.0,  280.0, 20.0),  # Aceite 460 ml (stock 195)
        24: (40.0,  200.0, 10.0),  # Aceite 1 L (stock 145)
        68: (50.0,  220.0, 10.0),  # Pasta Pura Cacao (stock 165)
        70: (40.0,  180.0, 10.0),  # Manteca de Cacao (stock 132)
    }
    ops = call(m, db, uid, pwd, "stock.warehouse.orderpoint", "search_read", [[]], {"fields": ["id", "product_id"]})
    updated_ops = 0
    for op in ops:
        pid = op["product_id"][0]
        if pid in new_rules:
            qmin, qmax, qmult = new_rules[pid]
            call(m, db, uid, pwd, "stock.warehouse.orderpoint", "write", [[op["id"]], {
                "product_min_qty": qmin,
                "product_max_qty": qmax,
                "qty_multiple": qmult,
            }])
            updated_ops += 1
    print(f"[OK] Actualizadas {updated_ops} reglas de reabastecimiento a escalas coherentes.")

    # 6. Verificación final
    prods = call(
        m, db, uid, pwd, "product.product", "search_read",
        [[["type", "=", "product"], ["active", "=", True]]],
        {"fields": ["name", "qty_available", "list_price", "standard_price", "sale_ok"], "order": "name asc"}
    )
    print(f"\n=== INVENTARIO FINAL NORMALIZADO ({len(prods)} productos) ===")
    for p in prods:
        tipo = "VENTA" if p["sale_ok"] else "INSUMO"
        print(f"  [{tipo:6}] {p['name']:58} | Stock: {p['qty_available']:6.0f} | Costo: S/{p['standard_price']:6.2f} | Precio: S/{p['list_price']:6.2f}")


if __name__ == "__main__":
    main()

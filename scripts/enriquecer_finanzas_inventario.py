#!/usr/bin/env python3
"""
Enriquece Odoo 17 con datos realistas para sustentación de Finanzas e Inventario:
- 10 Facturas de Proveedores (6 pagadas por Banco, 4 por pagar / cuentas por pagar)
- 1 Nota de Crédito de Cliente (devolución parcial por daño en transporte)
- 10 Reglas de Reabastecimiento (Stock Mínimo / Máximo) en Inventario
- 1 Orden de Compra confirmada con Recepción lista para validar en vivo
- 1 Orden de Manufactura confirmada lista para producir en vivo
- Limpieza de PO borrador en S/ 0.00
"""

from datetime import date, timedelta
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

    today = date.today()

    # 1. Limpiar PO borrador basura (S/ 0.00)
    draft_pos = call(m, db, uid, pwd, "purchase.order", "search", [[["state", "=", "draft"], ["amount_total", "=", 0]]])
    if draft_pos:
        call(m, db, uid, pwd, "purchase.order", "button_cancel", [draft_pos])
        call(m, db, uid, pwd, "purchase.order", "unlink", [draft_pos])
        print(f"[OK] Eliminadas {len(draft_pos)} POs borrador en S/ 0.00.")

    # 2. Facturas de Proveedores (in_invoice) - Cuentas por Pagar y Egresos
    existing_bills = call(m, db, uid, pwd, "account.move", "search_count", [[["move_type", "=", "in_invoice"], ["state", "=", "posted"]]])
    if existing_bills < 8:
        # Buscar diarios
        purchase_journal = call(m, db, uid, pwd, "account.journal", "search", [[["type", "=", "purchase"]]], {"limit": 1})[0]
        bank_journal = call(m, db, uid, pwd, "account.journal", "search", [[["type", "=", "bank"]]], {"limit": 1})[0]
        tax_igv_compra = 7  # 18% compra

        # Cuentas PCGE
        acc_mp = 809       # 6020000 Raw Materials
        acc_env = 813      # 6041000 Containers
        acc_emp = 814      # 6042000 Packaging
        acc_transp = 820   # 6092100 Transport linked to raw materials

        bills_spec = [
            # (partner_id, ref, days_ago, due_offset, pay_now, desc, product_id, qty, price_unit, account_id)
            (18, "F001-00004821", 38, 15, True,  "Coco Seco Criollo de Selva (Saco 50 kg) - Lote Oct-A", 48, 25, 120.0, acc_mp),
            (78, "F002-00001920", 32, 15, True,  "Cacao Criollo en Baba / Grano Fermentado (Saco 50 kg)", 49, 12, 450.0, acc_mp),
            (19, "F001-00008312", 28, 15, True,  "Frascos de Vidrio 250ml con tapa precintable (Caja x 50)", 52, 22, 70.0, acc_env),
            (80, "E001-00000945", 22, 10, True,  "Etiquetas Adhesivas Marca Coco Tropical (Rollo x 1000)", 59, 15, 85.0, acc_emp),
            (79, "F003-00003110", 16, 15, True,  "Bolsas Doypack Kraft con Zipper 250g (Millar)", 57, 9, 220.0, acc_emp),
            (83, "F001-00005590", 10, 10, True,  "Servicio de Transporte y Flete Refrigerado Satipo - Lima", False, 1, 1450.0, acc_transp),
            # 4 Pendientes de pago (Cuentas por Pagar: 1 vencida + 3 vigentes)
            (18, "F001-00005104", 20, -4, False, "Coco Seco Criollo de Selva (Saco 50 kg) - Lote Nov-A", 48, 18, 120.0, acc_mp),
            (78, "F002-00002108", 8,  12, False, "Cacao Criollo en Baba / Grano Fermentado (Saco 50 kg)", 49, 8,  450.0, acc_mp),
            (20, "F001-00007201", 5,  18, False, "Baldes Plásticos Grado Alimentario 20L (Pack x 10)", 56, 10, 140.0, acc_env),
            (82, "F004-00001189", 2,  25, False, "Frascos de Vidrio 1L con tapa precintable (Caja x 25)", 54, 20, 68.0, acc_env),
        ]

        created_bills = 0
        paid_bills = 0
        for partner_id, ref, days_ago, due_offset, pay_now, desc, prod_id, qty, price, acc_id in bills_spec:
            inv_date = today - timedelta(days=days_ago)
            due_date = today + timedelta(days=due_offset) if not pay_now else inv_date + timedelta(days=15)
            line_vals = {
                "name": desc,
                "quantity": qty,
                "price_unit": price,
                "account_id": acc_id,
                "tax_ids": [(6, 0, [tax_igv_compra])],
            }
            if prod_id:
                line_vals["product_id"] = prod_id

            move_id = call(m, db, uid, pwd, "account.move", "create", [{
                "move_type": "in_invoice",
                "partner_id": partner_id,
                "journal_id": purchase_journal,
                "l10n_latam_document_type_id": 1,
                "l10n_latam_document_number": ref,
                "ref": ref,
                "invoice_date": inv_date.isoformat(),
                "invoice_date_due": due_date.isoformat(),
                "invoice_line_ids": [(0, 0, line_vals)],
            }])
            call(m, db, uid, pwd, "account.move", "action_post", [[move_id]])
            created_bills += 1

            if pay_now:
                pay_date = inv_date + timedelta(days=3)
                wiz_id = call(
                    m, db, uid, pwd, "account.payment.register", "create",
                    [{"journal_id": bank_journal, "payment_date": pay_date.isoformat()}],
                    {"context": {"active_model": "account.move", "active_ids": [move_id]}}
                )
                call(m, db, uid, pwd, "account.payment.register", "action_create_payments", [[wiz_id]])
                paid_bills += 1

        print(f"[OK] Creadas {created_bills} Facturas de Proveedores ({paid_bills} pagadas por Banco, {created_bills - paid_bills} por pagar).")
    else:
        print(f"[SKIP] Ya existen {existing_bills} facturas de proveedores publicadas.")

    # 3. Nota de Crédito de Cliente (out_refund)
    existing_refunds = call(m, db, uid, pwd, "account.move", "search_count", [[["move_type", "=", "out_refund"], ["state", "=", "posted"]]])
    if existing_refunds == 0:
        # Buscar un cliente real con factura
        inv_sample = call(m, db, uid, pwd, "account.move", "search_read", [[["move_type", "=", "out_invoice"], ["state", "=", "posted"]]], {"fields": ["partner_id", "journal_id"], "limit": 1})
        if inv_sample:
            partner_id = inv_sample[0]["partner_id"][0]
            sale_journal = inv_sample[0]["journal_id"][0]
            refund_id = call(m, db, uid, pwd, "account.move", "create", [{
                "move_type": "out_refund",
                "partner_id": partner_id,
                "journal_id": 10,  # Factura Electrónica F001
                "l10n_latam_document_type_id": 7,  # Nota de Crédito (07)
                "l10n_latam_document_number": "FC01-00000001",
                "ref": "Devolución parcial (2 frascos dañados en tránsito)",
                "invoice_date": (today - timedelta(days=3)).isoformat(),
                "invoice_line_ids": [(0, 0, {
                    "product_id": 22,  # Aceite de Coco Virgen 250 ml
                    "name": "Nota de Crédito: Devolución 2 unid. Aceite de Coco Virgen 250 ml (daño transporte)",
                    "quantity": 2,
                    "price_unit": 20.0,
                    "tax_ids": [(6, 0, [1])],  # 18% IGV venta
                })],
            }])
            call(m, db, uid, pwd, "account.move", "action_post", [[refund_id]])
            print(f"[OK] Creada y publicada Nota de Crédito ID={refund_id}.")

    # 4. Reglas de Reabastecimiento (stock.warehouse.orderpoint)
    existing_ops = call(m, db, uid, pwd, "stock.warehouse.orderpoint", "search_count", [[]])
    if existing_ops == 0:
        # (product_id, min_qty, max_qty, qty_multiple)
        rules = [
            (48, 50.0,  300.0, 10.0),  # Coco Seco Criollo (Saco 50kg)
            (49, 40.0,  250.0, 5.0),   # Cacao Criollo (Saco 50kg)
            (52, 80.0,  400.0, 10.0),  # Frascos Vidrio 250ml
            (53, 60.0,  300.0, 10.0),  # Frascos Vidrio 460ml
            (59, 50.0,  250.0, 5.0),   # Etiquetas Coco Tropical
            (22, 100.0, 500.0, 25.0),  # Aceite de Coco Virgen 250 ml
            (23, 80.0,  400.0, 20.0),  # Aceite de Coco Virgen 460 ml
            (24, 60.0,  300.0, 10.0),  # Aceite de Coco Virgen 1 L
            (68, 50.0,  250.0, 10.0),  # Pasta Pura de Cacao 100% (250g)
            (70, 40.0,  200.0, 10.0),  # Manteca de Cacao Orgánica Virgen (250g)
        ]
        created_rules = 0
        for pid, qmin, qmax, qmult in rules:
            call(m, db, uid, pwd, "stock.warehouse.orderpoint", "create", [{
                "product_id": pid,
                "product_min_qty": qmin,
                "product_max_qty": qmax,
                "qty_multiple": qmult,
                "warehouse_id": 1,
            }])
            created_rules += 1
        print(f"[OK] Creadas {created_rules} Reglas de Reabastecimiento (Stock Mínimo/Máximo).")
    else:
        print(f"[SKIP] Ya existen {existing_ops} reglas de reabastecimiento.")

    # 5. Orden de Compra confirmada con Recepción lista para validar EN VIVO
    pending_in = call(m, db, uid, pwd, "stock.picking", "search_read", [[["picking_type_code", "=", "incoming"], ["state", "=", "assigned"]]], {"fields": ["id", "name", "origin"]})
    demo_po_exists = any("DEMO" in (p.get("origin") or "") for p in pending_in)
    if len(pending_in) < 2:
        po_id = call(m, db, uid, pwd, "purchase.order", "create", [{
            "partner_id": 18,  # Asociación Agroecológica de Productores de Coco San Martín
            "partner_ref": "OC-DEMO-RECEP-01",
            "order_line": [
                (0, 0, {
                    "product_id": 48,  # Coco Seco Criollo (Saco 50kg)
                    "name": "Coco Seco Criollo de Selva (Saco 50 kg) - Reposición Planta",
                    "product_qty": 10.0,
                    "price_unit": 120.0,
                    "taxes_id": [(6, 0, [7])],
                }),
                (0, 0, {
                    "product_id": 52,  # Frascos 250ml
                    "name": "Frascos de Vidrio 250ml con tapa precintable (Caja x 50)",
                    "product_qty": 5.0,
                    "price_unit": 70.0,
                    "taxes_id": [(6, 0, [7])],
                }),
            ],
        }])
        call(m, db, uid, pwd, "purchase.order", "button_confirm", [[po_id]])
        po_name = call(m, db, uid, pwd, "purchase.order", "read", [[po_id], ["name"]])[0]["name"]
        print(f"[OK] Creada Orden de Compra {po_name} confirmada con Recepción lista para validar en vivo.")

    # 6. Orden de Manufactura confirmada lista para producir EN VIVO
    open_mo = call(m, db, uid, pwd, "mrp.production", "search_count", [[["state", "in", ["confirmed", "progress"]]]])
    if open_mo == 0:
        boms = call(m, db, uid, pwd, "mrp.bom", "search_read", [[["product_tmpl_id", "=", 22]]], {"fields": ["id"], "limit": 1})
        bom_id = boms[0]["id"] if boms else False
        mo_vals = {
            "product_id": 22,  # Aceite de Coco Virgen 250 ml
            "product_qty": 25.0,
            "origin": "Lote Demo Sustentación",
        }
        if bom_id:
            mo_vals["bom_id"] = bom_id
        mo_id = call(m, db, uid, pwd, "mrp.production", "create", [mo_vals])
        call(m, db, uid, pwd, "mrp.production", "action_confirm", [[mo_id]])
        call(m, db, uid, pwd, "mrp.production", "action_assign", [[mo_id]])
        mo_name = call(m, db, uid, pwd, "mrp.production", "read", [[mo_id], ["name"]])[0]["name"]
        print(f"[OK] Creada Orden de Manufactura {mo_name} (25 unid. Aceite de Coco 250ml) lista para producir en vivo.")
    else:
        print(f"[SKIP] Ya existe {open_mo} orden de manufactura abierta.")

    # Resumen final
    print("\n=== RESUMEN FINAL ODOO 17 ===")
    for mtype, label in [("out_invoice", "Facturas Clientes"), ("in_invoice", "Facturas Proveedores"), ("out_refund", "Notas de Crédito")]:
        tot = call(m, db, uid, pwd, "account.move", "search_count", [[["move_type", "=", mtype], ["state", "=", "posted"]]])
        paid = call(m, db, uid, pwd, "account.move", "search_count", [[["move_type", "=", mtype], ["state", "=", "posted"], ["payment_state", "=", "paid"]]])
        unpaid = call(m, db, uid, pwd, "account.move", "search_count", [[["move_type", "=", mtype], ["state", "=", "posted"], ["payment_state", "in", ["not_paid", "partial"]]]])
        print(f"  {label}: total={tot} | pagadas={paid} | pendientes={unpaid}")
    print("  Reglas Reabastecimiento:", call(m, db, uid, pwd, "stock.warehouse.orderpoint", "search_count", [[]]))
    print("  Recepciones pendientes:", call(m, db, uid, pwd, "stock.picking", "search_count", [[["picking_type_code", "=", "incoming"], ["state", "=", "assigned"]]]))
    print("  Entregas pendientes:", call(m, db, uid, pwd, "stock.picking", "search_count", [[["picking_type_code", "=", "outgoing"], ["state", "in", ["assigned", "confirmed"]]]]))
    print("  Órdenes de Manufactura abiertas:", call(m, db, uid, pwd, "mrp.production", "search_count", [[["state", "in", ["confirmed", "progress"]]]]))


if __name__ == "__main__":
    main()

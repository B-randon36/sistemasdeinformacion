#!/usr/bin/env python3
"""
Demostración Punto de Venta (POS) con Arqueo de Caja - AGRO PERUVIAN FOODS S.A.C.
Configura 'Efectivo Soles' y 'Yape / Plin', abre sesión con fondo inicial S/ 150.00,
registra ventas cobradas en Efectivo Soles, Yape / Plin y pago mixto, y cierra con cuadre exacto.
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

    socket.setdefaulttimeout(30)
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

    # 1. Revisar si ya existe una sesión abierta con fondo S/ 150.00 (ej. POS/00002) para reutilizarla,
    #    o cerrar sesiones previas distintas y abrir una nueva con S/ 150.00.
    open_sessions = call(
        "pos.session",
        "search_read",
        [[["config_id", "=", 1], ["state", "!=", "closed"]]],
        {"fields": ["id", "name", "state", "cash_register_balance_start", "cash_register_balance_end"]},
    )
    sess_id = None
    sess_name = None
    for s in open_sessions:
        if abs(float(s.get("cash_register_balance_start") or 0.0) - 150.0) < 0.01 and s["state"] == "opened":
            sess_id = s["id"]
            sess_name = s["name"]
            print(f"[OK] Reutilizando sesión abierta {sess_name} (ID {sess_id}) con fondo S/ 150.00")
            continue
        sid = s["id"]
        sname = s["name"]
        expected = float(s.get("cash_register_balance_end") or s.get("cash_register_balance_start") or 0.0)
        print(f"Cerrando sesión previa {sname} (ID {sid}), balance esperado: S/ {expected:.2f}")
        if s["state"] == "opening_control":
            call("pos.session", "set_cashbox_pos", [[sid], float(s.get("cash_register_balance_start") or 100.0), "Apertura"])
        try:
            call("pos.session", "post_closing_cash_details", [[sid], expected])
        except Exception:
            call("pos.session", "write", [[sid], {"cash_register_balance_end_real": expected}])
        try:
            call("pos.session", "close_session_from_ui", [[sid]])
        except Exception:
            call("pos.session", "action_pos_session_closing_control", [[sid]])
            call("pos.session", "action_pos_session_close", [[sid]])
        print(f"[OK] Sesión previa {sname} cerrada.")

    # 2. Configurar métodos de pago solo si no hay sesión abierta reutilizada
    yape = call("pos.payment.method", "search_read", [[["name", "ilike", "Yape"]]], {"fields": ["id", "name"]})
    if yape:
        yape_id = yape[0]["id"]
    else:
        yape_id = call(
            "pos.payment.method",
            "create",
            [{"name": "Yape / Plin", "is_cash_count": False, "journal_id": 6}],
        )

    if not sess_id:
        call("pos.payment.method", "write", [[1], {"name": "Efectivo Soles"}])
        call("pos.config", "write", [[1], {"cash_control": True, "payment_method_ids": [(4, 1), (4, yape_id)]}])
    print(f"[OK] Métodos POS listos -> Efectivo Soles (ID 1) | Yape / Plin (ID {yape_id})")

    # 3. Abrir nueva sesión con fondo inicial S/ 150.00 si no había una abierta lista
    if not sess_id:
        sess_id = call("pos.session", "create", [{"config_id": 1, "user_id": uid}])
        call("pos.session", "set_cashbox_pos", [[sess_id], 150.0, "Fondo inicial de caja S/ 150.00 - Arqueo Planta/Feria"])
        sess = call(
            "pos.session",
            "search_read",
            [[["id", "=", sess_id]]],
            {"fields": ["id", "name", "state", "cash_register_balance_start"]},
        )[0]
        sess_name = sess["name"]
        print(f"[OK] Sesión abierta: {sess_name} | Fondo inicial: S/ {sess['cash_register_balance_start']:.2f}")

    # 4. Registrar 3 ventas POS (Efectivo Soles, Yape / Plin y Mixta)
    def crear_venta_pos(ref: str, lineas: List[tuple], pagos: List[tuple]) -> float:
        total_neto = sum(q * pu for _, _, q, pu in lineas)
        total_tax = round(total_neto * 0.18, 2)
        total_bruto = round(total_neto + total_tax, 2)
        order_lines = []
        for pid, pname, q, pu in lineas:
            sub = round(q * pu, 2)
            sub_incl = round(sub * 1.18, 2)
            order_lines.append((
                0,
                0,
                {
                    "product_id": pid,
                    "full_product_name": pname,
                    "qty": float(q),
                    "price_unit": float(pu),
                    "price_subtotal": sub,
                    "price_subtotal_incl": sub_incl,
                    "tax_ids": [(6, 0, [1])],
                },
            ))
        payment_lines = [
            (0, 0, {"payment_method_id": pm_id, "amount": round(float(amt), 2)})
            for pm_id, amt in pagos
        ]
        oid = call(
            "pos.order",
            "create",
            [
                {
                    "name": ref,
                    "session_id": sess_id,
                    "pos_reference": f"Pedido {ref}",
                    "amount_tax": total_tax,
                    "amount_total": total_bruto,
                    "amount_paid": total_bruto,
                    "amount_return": 0.0,
                    "lines": order_lines,
                    "payment_ids": payment_lines,
                    "state": "paid",
                }
            ],
        )
        print(f"  [POS ORDER] {ref} (ID {oid}) | Total c/IGV: S/ {total_bruto:.2f} | Pagos: {pagos}")
        return total_bruto

    # Venta 1: Efectivo Soles -> 2x20 + 2x14 = 68 * 1.18 = 80.24
    crear_venta_pos(
        f"{sess_name}-001",
        [(22, "Aceite de Coco Virgen 250 ml", 2, 20.0), (27, "Cacao Grano Entero Sin Tostar 500g", 2, 14.0)],
        [(1, 80.24)],
    )
    # Venta 2: Yape / Plin -> 1x65 + 2x16 = 97 * 1.18 = 114.46
    crear_venta_pos(
        f"{sess_name}-002",
        [(24, "Aceite de Coco Virgen 1 L", 1, 65.0), (30, "Coco Rallado Doypack 500g", 2, 16.0)],
        [(yape_id, 114.46)],
    )
    # Venta 3: Mixta (S/ 50.00 Efectivo Soles + S/ 68.00 Yape / Plin = S/ 118.00)
    crear_venta_pos(
        f"{sess_name}-003",
        [(22, "Aceite de Coco Virgen 250 ml", 5, 20.0)],
        [(1, 50.00), (yape_id, 68.00)],
    )

    # 5. Cerrar sesión con arqueo exacto
    sess_pre = call(
        "pos.session",
        "search_read",
        [[["id", "=", sess_id]]],
        {"fields": ["cash_register_balance_start", "cash_register_balance_end"]},
    )[0]
    expected_cash = float(sess_pre["cash_register_balance_end"])
    try:
        call("pos.session", "post_closing_cash_details", [[sess_id], expected_cash])
    except Exception:
        call("pos.session", "write", [[sess_id], {"cash_register_balance_end_real": expected_cash}])
    try:
        call("pos.session", "close_session_from_ui", [[sess_id]])
    except Exception:
        call("pos.session", "action_pos_session_closing_control", [[sess_id]])
        call("pos.session", "action_pos_session_close", [[sess_id]])

    sess_final = call(
        "pos.session",
        "search_read",
        [[["id", "=", sess_id]]],
        {
            "fields": [
                "id",
                "name",
                "state",
                "cash_register_balance_start",
                "cash_register_balance_end",
                "cash_register_balance_end_real",
                "cash_register_difference",
                "total_payments_amount",
            ]
        },
    )[0]
    print("\n========================================================================")
    print("ARQUEO DE CAJA POS COMPLETADO")
    print("========================================================================")
    print(f"  Sesión:                 {sess_final['name']} (Estado: {sess_final['state']})")
    print(f"  Fondo Inicial Efectivo: S/ {sess_final['cash_register_balance_start']:,.2f}")
    print(f"  Efectivo Esperado:      S/ {sess_final['cash_register_balance_end']:,.2f}")
    print(f"  Efectivo Contado Real:  S/ {sess_final['cash_register_balance_end_real']:,.2f}")
    print(f"  Diferencia de Arqueo:   S/ {sess_final['cash_register_difference']:,.2f}")
    print(f"  Total Ventas Sesión:    S/ {sess_final['total_payments_amount']:,.2f} (Efectivo Soles + Yape / Plin)")
    print("========================================================================")


if __name__ == "__main__":
    main()

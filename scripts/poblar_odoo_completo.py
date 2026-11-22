#!/usr/bin/env python3
"""
Script de Poblamiento Integral Odoo 17 ERP - AGRO PERUVIAN FOODS S.A.C.
(Solo librería estándar de Python: xmlrpc.client, sin dependencias externas)

Realiza en orden:
  1. Conectar E-commerce (website_sale) con Stock de Manufactura (mrp).
  2. Abastecer materias primas (stock.quant) y ejecutar órdenes de manufactura (mrp.production).
  3. Generar 125 ventas reales (sale.order) en los últimos 60 días, confirmar y validar entregas (stock.picking).
  4. Facturar 100 pedidos (account.move con IGV 18% y action_post) y dejar ~25 pendientes para Cuentas por Cobrar.
  5. Imprimir verificación final asegurando 0 stock negativo y >100 ventas confirmadas.
"""

import argparse
import datetime
import os
import random
import socket
import sys
import xmlrpc.client
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Utilidades de configuración (.env sin librerías externas)
# ---------------------------------------------------------------------------
def cargar_env(ruta_env: Path) -> Dict[str, str]:
    valores: Dict[str, str] = {}
    if not ruta_env.exists():
        return valores
    for linea in ruta_env.read_text(encoding="utf-8", errors="ignore").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        valores[k.strip()] = v.strip().strip('"').strip("'")
    return valores


class OdooClient:
    def __init__(self, url: str, db: str, user: str, password: str, timeout: int = 30):
        self.url = url.rstrip("/")
        self.db = db
        self.user = user
        self.password = password
        socket.setdefaulttimeout(timeout)
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
        self.uid: Optional[int] = None

    def conectar(self) -> int:
        version = self.common.version()
        uid = self.common.authenticate(self.db, self.user, self.password, {})
        if not uid:
            raise RuntimeError(
                f"Autenticación fallida en {self.url} (BD: '{self.db}', Usuario: '{self.user}'). "
                "Verifica tus credenciales o usa --url, --db, --user, --password."
            )
        self.uid = uid
        print(f"[OK] Conectado a Odoo {version.get('server_version')} en {self.url} | BD: {self.db} | UID: {uid}")
        return uid

    def call(self, model: str, method: str, args: list, kwargs: Optional[dict] = None) -> Any:
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password, model, method, args, kwargs or {}
            )
        except xmlrpc.client.Fault as fault:
            # En Odoo XML-RPC, los métodos que ejecutan con éxito y retornan Python None
            # disparan "cannot marshal None unless allow_none is enabled".
            if "cannot marshal None" in str(fault.faultString):
                return None
            raise

    def search_read(
        self, model: str, domain: list, fields: list, limit: int = 500, order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        kw: Dict[str, Any] = {"fields": fields, "limit": limit}
        if order:
            kw["order"] = order
        return self.call(model, "search_read", [domain], kw)

    def search_count(self, model: str, domain: list) -> int:
        return self.call(model, "search_count", [domain])

    def create(self, model: str, vals: dict, context: Optional[dict] = None) -> int:
        kw = {"context": context} if context else {}
        return self.call(model, "create", [vals], kw)

    def write(self, model: str, ids: List[int], vals: dict, context: Optional[dict] = None) -> bool:
        kw = {"context": context} if context else {}
        return self.call(model, "write", [ids, vals], kw)


# ---------------------------------------------------------------------------
# Helpers de negocio Odoo 17
# ---------------------------------------------------------------------------
def obtener_ubicacion_stock(odoo: OdooClient) -> int:
    locs = odoo.search_read(
        "stock.location",
        [["usage", "=", "internal"]],
        ["id", "name", "complete_name"],
        limit=20,
    )
    for loc in locs:
        if "existencias" in loc["name"].lower() or "stock" in loc["name"].lower():
            return loc["id"]
    if not locs:
        raise RuntimeError("No se encontró ninguna ubicación interna de stock en Odoo.")
    return locs[0]["id"]


def ajustar_stock_producto(odoo: OdooClient, product_id: int, location_id: int, nueva_cantidad: float) -> None:
    """Ajusta el inventario disponible de un producto en WH/Existencias usando stock.quant."""
    quants = odoo.search_read(
        "stock.quant",
        [["product_id", "=", product_id], ["location_id", "=", location_id]],
        ["id", "quantity"],
        limit=1,
    )
    if quants:
        quant_id = quants[0]["id"]
        odoo.write("stock.quant", [quant_id], {"inventory_quantity": nueva_cantidad})
    else:
        quant_id = odoo.create(
            "stock.quant",
            {
                "product_id": product_id,
                "location_id": location_id,
                "inventory_quantity": nueva_cantidad,
            },
        )
    odoo.call("stock.quant", "action_apply_inventory", [[quant_id]])


def seleccionar_boms_principales(odoo: OdooClient) -> Tuple[Dict[int, dict], Dict[int, dict], Dict[int, List[dict]]]:
    """
    Devuelve:
      - normal_boms_by_tmpl: {product_tmpl_id: bom} para BOMs de manufactura ('normal')
      - kit_boms_by_tmpl: {product_tmpl_id: bom} para BOMs tipo Kit ('phantom')
      - lines_by_bom: {bom_id: [bom_lines]}
    Deduplica por product_tmpl_id prefiriendo códigos oficiales LOM-/KIT- y menor ID.
    """
    boms = odoo.search_read(
        "mrp.bom",
        [],
        ["id", "code", "type", "product_tmpl_id", "product_id", "product_qty", "product_uom_id", "bom_line_ids"],
        order="id asc",
    )
    all_lines = odoo.search_read(
        "mrp.bom.line",
        [],
        ["id", "bom_id", "product_id", "product_qty"],
        limit=1000,
    )
    lines_by_bom: Dict[int, List[dict]] = {}
    for ln in all_lines:
        bid = ln["bom_id"][0]
        lines_by_bom.setdefault(bid, []).append(ln)

    normal_boms: Dict[int, dict] = {}
    kit_boms: Dict[int, dict] = {}

    for b in boms:
        tmpl_id = b["product_tmpl_id"][0]
        code = (b.get("code") or "").upper()
        if b["type"] == "phantom":
            if tmpl_id not in kit_boms or code.startswith("KIT-"):
                kit_boms[tmpl_id] = b
        else:
            if tmpl_id not in normal_boms:
                normal_boms[tmpl_id] = b
            elif code.startswith("LOM-") and not (normal_boms[tmpl_id].get("code") or "").upper().startswith("LOM-"):
                normal_boms[tmpl_id] = b

    return normal_boms, kit_boms, lines_by_bom


# ---------------------------------------------------------------------------
# TAREA 1: Conectar E-commerce con el Stock de Manufactura
# ---------------------------------------------------------------------------
def tarea_1_configurar_ecommerce(
    odoo: OdooClient, normal_boms: Dict[int, dict], kit_boms: Dict[int, dict]
) -> List[dict]:
    print("\n" + "=" * 72)
    print("TAREA 1: Conectando E-commerce con Stock de Manufactura (BOM)")
    print("=" * 72)

    tmpl_ids = sorted(set(normal_boms.keys()) | set(kit_boms.keys()))
    productos = odoo.search_read(
        "product.product",
        [["product_tmpl_id", "in", tmpl_ids], ["detailed_type", "=", "product"]],
        ["id", "name", "product_tmpl_id", "list_price", "qty_available", "uom_id", "taxes_id"],
    )
    if not productos:
        raise RuntimeError("No se encontraron productos almacenables (detailed_type='product') con BOM.")

    # Buscar ruta 'Manufacture' / 'Fabricar'
    routes = odoo.search_read("stock.route", [], ["id", "name"])
    mfg_route_id = None
    for r in routes:
        rname = r["name"].lower()
        if "manufactur" in rname or "fabric" in rname:
            mfg_route_id = r["id"]
            break

    # Verificar qué campos existen en product.template
    tmpl_fields = set(odoo.call("product.template", "fields_get", [], {"attributes": ["type"]}).keys())

    # Verificar impuesto IGV 18%
    taxes = odoo.search_read(
        "account.tax",
        [["type_tax_use", "=", "sale"], ["amount", "=", 18.0]],
        ["id", "name"],
        limit=1,
    )
    igv_tax_id = taxes[0]["id"] if taxes else None

    actualizados = 0
    for prod in productos:
        tid = prod["product_tmpl_id"][0]
        vals: Dict[str, Any] = {}
        if "website_published" in tmpl_fields:
            vals["website_published"] = True
        if "allow_out_of_stock_order" in tmpl_fields:
            vals["allow_out_of_stock_order"] = False
        if "show_availability" in tmpl_fields:
            vals["show_availability"] = True
        if "available_threshold" in tmpl_fields:
            vals["available_threshold"] = 10000.0
        if mfg_route_id and tid in normal_boms:
            vals["route_ids"] = [(4, mfg_route_id)]
        if igv_tax_id and not prod.get("taxes_id"):
            vals["taxes_id"] = [(6, 0, [igv_tax_id])]

        if vals:
            odoo.write("product.template", [tid], vals)
            actualizados += 1
            tipo = "BOM Manufactura" if tid in normal_boms else "BOM Kit Mayorista"
            print(f"  [E-COMMERCE] {prod['name']} ({tipo}) -> publicado, sin venta sin stock, disponibilidad visible")

    print(f"[OK] Tarea 1 completada: {actualizados} productos configurados en E-commerce.")
    return productos


# ---------------------------------------------------------------------------
# TAREA 2: Abastecer Insumos y Ejecutar Órdenes de Manufactura
# ---------------------------------------------------------------------------
def tarea_2_abastecer_y_manufacturar(
    odoo: OdooClient,
    productos_bom: List[dict],
    normal_boms: Dict[int, dict],
    kit_boms: Dict[int, dict],
    lines_by_bom: Dict[int, List[dict]],
    qty_base: int = 600,
) -> int:
    print("\n" + "=" * 72)
    print("TAREA 2: Abasteciendo Insumos y Ejecutando Órdenes de Manufactura")
    print("=" * 72)

    location_id = obtener_ubicacion_stock(odoo)
    print(f"  Ubicación interna detectada: ID {location_id}")

    # 2.1 Identificar todos los insumos (componentes de BOMs normales) y componentes de kits
    finished_prod_ids: Set[int] = {p["id"] for p in productos_bom}
    raw_material_ids: Set[int] = set()
    kit_component_ids: Set[int] = set()

    for b in normal_boms.values():
        for ln in lines_by_bom.get(b["id"], []):
            cid = ln["product_id"][0]
            if cid not in finished_prod_ids:
                raw_material_ids.add(cid)

    for b in kit_boms.values():
        for ln in lines_by_bom.get(b["id"], []):
            kit_component_ids.add(ln["product_id"][0])

    # 2.2 Limpiar cualquier stock negativo en insumos o kits antes de manufacturar
    print("  -> Verificando y abasteciendo materias primas (>= 5,000 uds por insumo)...")
    if raw_material_ids:
        raw_prods = odoo.search_read(
            "product.product",
            [["id", "in", sorted(raw_material_ids)]],
            ["id", "name", "qty_available", "detailed_type"],
        )
        for rp in raw_prods:
            if rp["detailed_type"] != "product":
                continue
            target_qty = max(5000.0, float(rp["qty_available"]) + 5000.0) if rp["qty_available"] < 5000.0 else float(rp["qty_available"])
            if rp["qty_available"] < 5000.0:
                ajustar_stock_producto(odoo, rp["id"], location_id, target_qty)
                print(f"     [INSUMO] {rp['name']}: {rp['qty_available']} -> {target_qty}")

    # Limpiar quants negativos residuales únicamente en productos sin BOM (ni normal ni kit).
    # Nota: en Odoo 17 el stock de un Kit (phantom) se calcula automáticamente desde sus componentes.
    neg_prods = odoo.search_read(
        "product.product",
        [["detailed_type", "=", "product"], ["qty_available", "<", 0]],
        ["id", "name", "qty_available", "product_tmpl_id"],
    )
    for np in neg_prods:
        tid = np["product_tmpl_id"][0]
        if tid not in normal_boms and tid not in kit_boms:
            ajustar_stock_producto(odoo, np["id"], location_id, 5000.0)
            print(f"     [AJUSTE NEGATIVO] {np['name']}: {np['qty_available']} -> 5000.0")

    # 2.3 Crear, confirmar y completar órdenes de manufactura (mrp.production) para cada BOM normal
    prod_by_tmpl = {p["product_tmpl_id"][0]: p for p in productos_bom}
    mo_completadas = 0

    print(f"  -> Creando órdenes de manufactura (base {qty_base} uds; 1,000 uds para productos usados en Kits)...")
    for tid, bom in sorted(normal_boms.items()):
        prod = prod_by_tmpl.get(tid)
        if not prod:
            continue

        # Si el producto es componente de Bandejas Mayoristas (Kit x24/x12/x6), fabricamos 1,000 uds
        qty_to_produce = max(qty_base, 1000) if prod["id"] in kit_component_ids else qty_base
        # Si tenía stock negativo previo, compensamos adicionalmente
        if prod["qty_available"] < 0:
            qty_to_produce += int(abs(prod["qty_available"])) + 50

        mo_vals = {
            "product_id": prod["id"],
            "product_qty": float(qty_to_produce),
            "product_uom_id": prod["uom_id"][0],
            "bom_id": bom["id"],
            "origin": "PLAN-PROD-2026-BSC",
        }
        mo_id = odoo.create("mrp.production", mo_vals)
        odoo.call("mrp.production", "action_confirm", [[mo_id]])

        # Marcar cantidades consumidas y producidas (Odoo 17: quantity + picked=True)
        odoo.write("mrp.production", [mo_id], {"qty_producing": float(qty_to_produce)})
        mo_data = odoo.search_read("mrp.production", [["id", "=", mo_id]], ["name", "move_raw_ids"])[0]
        if mo_data.get("move_raw_ids"):
            raw_moves = odoo.search_read(
                "stock.move",
                [["id", "in", mo_data["move_raw_ids"]]],
                ["id", "product_uom_qty"],
            )
            for rm in raw_moves:
                odoo.write(
                    "stock.move",
                    [rm["id"]],
                    {"quantity": rm["product_uom_qty"], "picked": True},
                )

        res = odoo.call(
            "mrp.production",
            "button_mark_done",
            [[mo_id]],
            {"context": {"skip_backorder": True, "skip_consumption": True}},
        )
        # Si Odoo retorna un wizard de consumo/backorder, confirmarlo automáticamente
        if isinstance(res, dict) and res.get("res_model") and res.get("res_id"):
            wiz_model = res["res_model"]
            wiz_id = res["res_id"]
            for meth in ("action_confirm", "process"):
                try:
                    odoo.call(wiz_model, meth, [[wiz_id]])
                    break
                except Exception:
                    continue

        mo_completadas += 1
        print(f"     [MRP DONE] {mo_data['name']} | {prod['name']} -> +{qty_to_produce} uds fabricadas")

    print(f"[OK] Tarea 2 completada: {mo_completadas} órdenes de manufactura finalizadas.")
    return mo_completadas


# ---------------------------------------------------------------------------
# TAREA 3: Generar 125 Ventas Reales distribuidas en los últimos 60 días
# ---------------------------------------------------------------------------
def validar_entregas_pedido(odoo: OdooClient, order_id: int) -> int:
    """Confirma y valida los stock.picking salientes de un sale.order en Odoo 17."""
    order_info = odoo.search_read("sale.order", [["id", "=", order_id]], ["picking_ids"])[0]
    picking_ids = order_info.get("picking_ids") or []
    validadas = 0

    for pid in picking_ids:
        pk = odoo.search_read("stock.picking", [["id", "=", pid]], ["id", "name", "state", "move_ids"])[0]
        if pk["state"] in ("done", "cancel"):
            validadas += 1
            continue
        if pk["state"] in ("confirmed", "waiting"):
            odoo.call("stock.picking", "action_assign", [[pid]])

        move_ids = pk.get("move_ids") or []
        if move_ids:
            moves = odoo.search_read("stock.move", [["id", "in", move_ids]], ["id", "product_uom_qty", "state"])
            for mv in moves:
                if mv["state"] not in ("done", "cancel"):
                    odoo.write("stock.move", [mv["id"]], {"quantity": mv["product_uom_qty"], "picked": True})

        res = odoo.call(
            "stock.picking",
            "button_validate",
            [[pid]],
            {"context": {"skip_backorder": True, "skip_sms": True}},
        )
        if isinstance(res, dict) and res.get("res_model") and res.get("res_id"):
            wiz_model = res["res_model"]
            wiz_id = res["res_id"]
            for meth in ("process", "process_cancel_backorder"):
                try:
                    odoo.call(wiz_model, meth, [[wiz_id]])
                    break
                except Exception:
                    continue
        validadas += 1

    return validadas


def tarea_3_generar_ventas(
    odoo: OdooClient,
    productos_bom: List[dict],
    kit_boms: Dict[int, dict],
    lines_by_bom: Dict[int, List[dict]],
    total_ventas: int = 125,
) -> List[Tuple[int, str]]:
    print("\n" + "=" * 72)
    print(f"TAREA 3: Generando {total_ventas} Ventas Reales (últimos 60 días) y Validando Entregas")
    print("=" * 72)

    # 3.1 Clientes reales con RUC/DNI
    clientes = odoo.search_read(
        "res.partner",
        [["customer_rank", ">", 0], ["vat", "!=", False]],
        ["id", "name", "vat"],
    )
    clientes = [c for c in clientes if "AGRO PERUVIAN" not in (c["name"] or "").upper()]
    if not clientes:
        clientes = odoo.search_read("res.partner", [["customer_rank", ">", 0]], ["id", "name", "vat"])
    if not clientes:
        raise RuntimeError("No hay clientes registrados en res.partner.")

    # 3.2 Refrescar stock disponible real tras la manufactura
    prod_ids = [p["id"] for p in productos_bom]
    prods_live = odoo.search_read(
        "product.product",
        [["id", "in", prod_ids]],
        ["id", "name", "product_tmpl_id", "list_price", "qty_available", "taxes_id"],
    )
    stock_restante: Dict[int, float] = {p["id"]: float(p["qty_available"]) for p in prods_live}

    # Mapa de explosión para kits (phantom) -> {kit_prod_id: [(comp_prod_id, qty_por_kit), ...]}
    kit_explosion: Dict[int, List[Tuple[int, float]]] = {}
    for p in prods_live:
        tid = p["product_tmpl_id"][0]
        if tid in kit_boms:
            bom = kit_boms[tid]
            kit_explosion[p["id"]] = [
                (ln["product_id"][0], float(ln["product_qty"]) / float(bom.get("product_qty") or 1.0))
                for ln in lines_by_bom.get(bom["id"], [])
            ]

    # Impuesto IGV 18%
    taxes = odoo.search_read(
        "account.tax", [["type_tax_use", "=", "sale"], ["amount", "=", 18.0]], ["id", "name"], limit=1
    )
    igv_tax_id = taxes[0]["id"] if taxes else None

    # 3.3 Generar fechas aleatorias ordenadas cronológicamente en los últimos 60 días
    ahora = datetime.datetime.now()
    fechas = sorted(
        ahora - datetime.timedelta(
            days=random.randint(0, 59),
            hours=random.randint(0, 10),
            minutes=random.randint(0, 59),
        )
        for _ in range(total_ventas)
    )

    ordenes_creadas: List[Tuple[int, str]] = []
    # Mantener margen de seguridad mínimo de 10 unidades por producto para nunca acercarse a 0
    MARGEN_SEGURIDAD = 10.0

    for idx, fecha_dt in enumerate(fechas, start=1):
        cliente = random.choice(clientes)
        fecha_str = fecha_dt.strftime("%Y-%m-%d %H:%M:%S")
        fecha_solo = fecha_dt.strftime("%Y-%m-%d")

        # Elegir 1 o 2 líneas con productos que tengan stock disponible suficiente
        num_lineas = random.choice([1, 1, 2])
        candidatos = prods_live[:]
        random.shuffle(candidatos)

        order_lines = []
        usados_en_orden: Set[int] = set()

        for prod in candidatos:
            if len(order_lines) >= num_lineas:
                break
            pid = prod["id"]
            if pid in usados_en_orden:
                continue

            es_kit = pid in kit_explosion
            qty = random.randint(1, 2) if es_kit else random.randint(1, 5)

            # Verificar stock disponible (o de los componentes si es kit)
            if es_kit:
                puede = all(
                    stock_restante.get(cid, 0.0) - (cqty * qty) >= MARGEN_SEGURIDAD
                    for cid, cqty in kit_explosion[pid]
                )
            else:
                puede = stock_restante.get(pid, 0.0) - qty >= MARGEN_SEGURIDAD

            if not puede:
                continue

            # Reservar en memoria
            if es_kit:
                for cid, cqty in kit_explosion[pid]:
                    stock_restante[cid] = stock_restante.get(cid, 0.0) - (cqty * qty)
            else:
                stock_restante[pid] = stock_restante.get(pid, 0.0) - qty

            usados_en_orden.add(pid)
            price = prod["list_price"] if prod["list_price"] > 0 else 25.0
            line_vals: Dict[str, Any] = {
                "product_id": pid,
                "product_uom_qty": float(qty),
                "price_unit": float(price),
            }
            if igv_tax_id:
                line_vals["tax_id"] = [(6, 0, [igv_tax_id])]
            order_lines.append((0, 0, line_vals))

        if not order_lines:
            print(f"  [WARN] Sin stock suficiente en iteración {idx}, omitiendo.")
            continue

        so_id = odoo.create(
            "sale.order",
            {
                "partner_id": cliente["id"],
                "date_order": fecha_str,
                "order_line": order_lines,
                "origin": "VENTA-HISTORICA-BSC",
            },
        )
        odoo.call("sale.order", "action_confirm", [[so_id]])
        # Restaurar fecha histórica (action_confirm sobreescribe date_order con now())
        odoo.write("sale.order", [so_id], {"date_order": fecha_str})
        validar_entregas_pedido(odoo, so_id)

        ordenes_creadas.append((so_id, fecha_solo))
        if idx % 25 == 0 or idx == total_ventas:
            print(f"  [VENTAS] Progreso: {idx}/{total_ventas} órdenes confirmadas y entregadas...")

    print(f"[OK] Tarea 3 completada: {len(ordenes_creadas)} ventas confirmadas y entregas validadas.")
    return ordenes_creadas


# ---------------------------------------------------------------------------
# TAREA 4: Facturar ~100 pedidos y dejar ~25 pendientes de facturar/cobrar
# ---------------------------------------------------------------------------
def tarea_4_facturar_pedidos(
    odoo: OdooClient, ordenes_creadas: List[Tuple[int, str]], cantidad_facturar: int = 100
) -> Tuple[int, int]:
    print("\n" + "=" * 72)
    print(f"TAREA 4: Facturando {cantidad_facturar} Pedidos (IGV 18%) y Dejando Cartera Pendiente")
    print("=" * 72)

    a_facturar = ordenes_creadas[:cantidad_facturar]
    facturas_emitidas = 0
    facturas_pagadas = 0

    # De las 100 facturas emitidas, registramos pago en ~75 y dejamos ~25 emitidas por cobrar
    # (además de las 25 órdenes que quedan pendientes de facturar)
    limite_pagadas = int(len(a_facturar) * 0.75)

    # Buscar diario de banco/efectivo para registrar cobros
    pay_journals = odoo.search_read(
        "account.journal", [["type", "in", ["bank", "cash"]]], ["id", "name"], limit=1
    )
    pay_journal_id = pay_journals[0]["id"] if pay_journals else None

    for idx, (so_id, fecha_orden) in enumerate(a_facturar, start=1):
        try:
            ctx = {
                "active_model": "sale.order",
                "active_ids": [so_id],
                "active_id": so_id,
            }
            wiz_id = odoo.create(
                "sale.advance.payment.inv",
                {"advance_payment_method": "delivered"},
                context=ctx,
            )
            odoo.call("sale.advance.payment.inv", "create_invoices", [[wiz_id]], {"context": ctx})

            so_info = odoo.search_read("sale.order", [["id", "=", so_id]], ["invoice_ids"])[0]
            inv_ids = so_info.get("invoice_ids") or []
            for inv_id in inv_ids:
                inv = odoo.search_read("account.move", [["id", "=", inv_id]], ["state"])[0]
                if inv["state"] == "draft":
                    odoo.write("account.move", [inv_id], {"invoice_date": fecha_orden})
                    odoo.call("account.move", "action_post", [[inv_id]])
                    facturas_emitidas += 1

                    # Registrar pago en las primeras ~75 facturas para tener CxC realista (~25% por cobrar)
                    if idx <= limite_pagadas and pay_journal_id:
                        try:
                            p_ctx = {
                                "active_model": "account.move",
                                "active_ids": [inv_id],
                                "active_id": inv_id,
                            }
                            pw_id = odoo.create(
                                "account.payment.register",
                                {"journal_id": pay_journal_id, "payment_date": fecha_orden},
                                context=p_ctx,
                            )
                            odoo.call("account.payment.register", "action_create_payments", [[pw_id]], {"context": p_ctx})
                            facturas_pagadas += 1
                        except Exception:
                            pass

            if idx % 25 == 0 or idx == len(a_facturar):
                print(f"  [FACTURACION] Progreso: {idx}/{len(a_facturar)} pedidos facturados y publicados...")
        except Exception as e:
            print(f"  [WARN] Error facturando pedido ID {so_id}: {e}")

    pendientes_facturar = len(ordenes_creadas) - len(a_facturar)
    print(
        f"[OK] Tarea 4 completada: {facturas_emitidas} facturas publicadas "
        f"({facturas_pagadas} cobradas, {facturas_emitidas - facturas_pagadas} por cobrar) | "
        f"{pendientes_facturar} pedidos dejados pendientes de facturar."
    )
    return facturas_emitidas, facturas_pagadas


# ---------------------------------------------------------------------------
# RESUMEN FINAL DE VERIFICACIÓN
# ---------------------------------------------------------------------------
def imprimir_resumen_verificacion(odoo: OdooClient, productos_bom: List[dict]) -> None:
    print("\n" + "=" * 72)
    print("RESUMEN FINAL DE VERIFICACIÓN - AGRO PERUVIAN FOODS S.A.C. (ODOO 17)")
    print("=" * 72)

    total_ecom = odoo.search_count(
        "product.template",
        [["website_published", "=", True], ["allow_out_of_stock_order", "=", False]],
    )
    total_mrp_done = odoo.search_count("mrp.production", [["state", "=", "done"]])
    total_ventas_conf = odoo.search_count("sale.order", [["state", "in", ["sale", "done"]]])
    total_ventas_por_fact = odoo.search_count(
        "sale.order", [["state", "in", ["sale", "done"]], ["invoice_status", "=", "to invoice"]]
    )
    total_fact_posted = odoo.search_count(
        "account.move", [["move_type", "=", "out_invoice"], ["state", "=", "posted"]]
    )
    facturas_posted = odoo.search_read(
        "account.move",
        [["move_type", "=", "out_invoice"], ["state", "=", "posted"]],
        ["amount_total", "amount_residual"],
        limit=1000,
    )
    monto_facturado = sum(f.get("amount_total", 0.0) for f in facturas_posted)
    monto_por_cobrar = sum(f.get("amount_residual", 0.0) for f in facturas_posted)

    # Stock actual y verificación de negativos
    negativos = odoo.search_read(
        "product.product",
        [["detailed_type", "=", "product"], ["qty_available", "<", 0]],
        ["id", "name", "qty_available"],
    )
    prod_ids = [p["id"] for p in productos_bom]
    stock_final = odoo.search_read(
        "product.product",
        [["id", "in", prod_ids]],
        ["id", "name", "qty_available"],
        order="name asc",
    )

    print(f"  1. Productos publicados en E-commerce (sin venta sin stock): {total_ecom}")
    print(f"  2. Órdenes de manufactura completadas (state='done'):        {total_mrp_done}")
    print(f"  3. Ventas confirmadas totales (state='sale'/'done'):         {total_ventas_conf}")
    print(f"     -> Pedidos confirmados pendientes de facturar:            {total_ventas_por_fact}")
    print(f"  4. Facturas emitidas / publicadas (IGV 18%):                 {total_fact_posted}")
    print(f"     -> Monto Total Facturado:                                 S/ {monto_facturado:,.2f}")
    print(f"     -> Cuentas por Cobrar (Saldo Pendiente):                  S/ {monto_por_cobrar:,.2f}")
    print(f"  5. Productos con stock NEGATIVO en todo el inventario:       {len(negativos)}")

    if negativos:
        print("     [ALERTA] Productos en negativo detectados:")
        for n in negativos:
            print(f"       - {n['name']}: {n['qty_available']}")
    else:
        print("     [OK] ¡CERO productos con stock negativo! Inventario 100% cuadrado.")

    print("\n  --- Stock actual disponible de productos terminados con BOM ---")
    for sp in stock_final:
        print(f"     * {sp['name']:<55} : {sp['qty_available']:>8.2f} uds")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Poblar Odoo 17 Agro Peruvian Foods S.A.C. vía XML-RPC")
    env = cargar_env(Path(__file__).resolve().parent.parent / ".env")

    default_url = env.get("ODOO_URL", "http://52.86.231.75:8069")
    if "://odoo:" in default_url or "://localhost:" in default_url:
        default_url = "http://52.86.231.75:8069"

    parser.add_argument("--url", default=os.getenv("ODOO_URL_OVERRIDE", default_url), help="URL de Odoo 17")
    parser.add_argument("--db", default=os.getenv("ODOO_DB_OVERRIDE", env.get("ODOO_DB", "brandon")), help="Base de datos Odoo")
    parser.add_argument("--user", default=os.getenv("ODOO_USER_OVERRIDE", env.get("ODOO_USER", "destruller1025b@gmail.com")), help="Usuario Odoo")
    parser.add_argument("--password", default=os.getenv("ODOO_PASSWORD_OVERRIDE", env.get("ODOO_PASSWORD", "")), help="Contraseña Odoo")
    parser.add_argument("--orders", type=int, default=125, help="Cantidad de ventas a generar (default: 125)")
    parser.add_argument("--invoice-count", type=int, default=100, help="Cantidad de ventas a facturar (default: 100)")
    parser.add_argument("--qty-manufacture", type=int, default=600, help="Unidades base a fabricar por producto BOM (default: 600)")
    args = parser.parse_args()

    odoo = OdooClient(args.url, args.db, args.user, args.password, timeout=45)
    odoo.conectar()

    normal_boms, kit_boms, lines_by_bom = seleccionar_boms_principales(odoo)
    print(f"  BOMs detectadas -> Manufactura normal: {len(normal_boms)} | Kits Mayoristas: {len(kit_boms)}")

    productos_bom = tarea_1_configurar_ecommerce(odoo, normal_boms, kit_boms)
    tarea_2_abastecer_y_manufacturar(
        odoo, productos_bom, normal_boms, kit_boms, lines_by_bom, qty_base=args.qty_manufacture
    )
    ordenes_creadas = tarea_3_generar_ventas(
        odoo, productos_bom, kit_boms, lines_by_bom, total_ventas=args.orders
    )
    tarea_4_facturar_pedidos(odoo, ordenes_creadas, cantidad_facturar=args.invoice_count)
    imprimir_resumen_verificacion(odoo, productos_bom)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[ERROR FATAL] {exc}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
Configura en Odoo 17 para AGRO PERUVIAN FOODS S.A.C.:
  1. Términos y Condiciones de Venta completos en español (/terms -> res.company.invoice_terms_html).
  2. Filtros nativos en /shop sin alterar variantes ni stock (create_variant='no_variant'):
       - Derivado de: Coco | Cacao
       - Modalidad de Compra: Minorista | Mayorista (B2B)
       - Tipo de Producto: Aceite de Coco Virgen | Cacao Criollo y Derivados | Coco Rallado y Harina
     + Etiquetas visibles en e-commerce: Prensado en Frío, Sin Gluten / Keto, 100% Orgánico.
  3. Potenciación del buscador global y de tienda (placeholder descriptivo, SKUs y palabras clave).
"""

import socket
import xmlrpc.client
from pathlib import Path
from typing import Any, Dict, List


TERMS_HTML = """
<div class="py-3">
    <div class="p-4 mb-4 rounded-3 text-white" style="background: linear-gradient(115deg, #3D2314 0%, #2D5A27 100%);">
        <h1 class="fw-bold mb-2 text-white">Términos y Condiciones de Venta</h1>
        <p class="mb-0" style="color: #f3efe9;">
            <strong>AGRO PERUVIAN FOODS S.A.C.</strong> &bull; RUC: 20609060876 &bull; Puente Piedra, Lima - Perú
        </p>
    </div>

    <p class="text-muted">
        Última actualización: Noviembre 2026. Al realizar una compra o solicitar una cotización a través de nuestra tienda online o canales comerciales, el cliente acepta los presentes Términos y Condiciones.
    </p>

    <ol class="lh-lg">
        <li class="mb-3">
            <strong>Identificación del Proveedor:</strong>
            AGRO PERUVIAN FOODS S.A.C., identificada con RUC N.° <strong>20609060876</strong>, con domicilio comercial en Asoc. Los Sauces Mz. E Lote 22 (cerca al Río Chillón - Puente de Madera), Puente Piedra, Lima - Perú; correo electrónico <a href="mailto:agroperuvianfoods@gmail.com">agroperuvianfoods@gmail.com</a> y teléfono/WhatsApp <a href="tel:+51991215347">+51 991 215 347</a>.
        </li>
        <li class="mb-3">
            <strong>Productos Naturales y Disponibilidad de Stock:</strong>
            Comercializamos derivados 100% naturales de coco y cacao criollo peruano (aceite de coco virgen prensado en frío, coco rallado, harina de coco sin gluten, cacao en grano, pasta pura, nibs y manteca de cacao), libres de aditivos y preservantes. El stock mostrado en la tienda se encuentra sincronizado en tiempo real con nuestro sistema ERP y planta de manufactura.
        </li>
        <li class="mb-3">
            <strong>Modalidades de Compra (Minorista y Mayorista B2B):</strong>
            Atendemos tanto a consumidores finales en formato <strong>Minorista</strong> (frascos de 30 ml a 1 L y bolsas doypack de 150 g a 1 kg) como a bio tiendas, restaurantes, hoteles y distribuidores en formato <strong>Mayorista (B2B)</strong> (baldes de 4 L y 20 L, y bandejas mayoristas x6, x12 y x24 unidades).
        </li>
        <li class="mb-3">
            <strong>Precios, Moneda y Facturación Electrónica SUNAT:</strong>
            Todos los precios publicados están expresados en Soles (<strong>S/ PEN</strong>) e incluyen el Impuesto General a las Ventas (<strong>IGV 18%</strong>). Por cada compra emitimos <strong>Boleta o Factura Electrónica</strong> validada ante SUNAT, cuyo comprobante PDF con código QR se entrega al cliente al confirmarse la operación.
        </li>
        <li class="mb-3">
            <strong>Plazos y Condiciones de Envío (Delivery a Todo el Perú):</strong>
            <ul>
                <li><strong>Lima o provincias cercanas:</strong> entrega en un plazo máximo de <strong>2 días hábiles</strong> desde la confirmación del pedido y pago.</li>
                <li><strong>Demás regiones del Perú:</strong> entrega entre <strong>2 a 7 días hábiles</strong> mediante operador logístico o courier autorizado, según el destino.</li>
            </ul>
            El cliente es responsable de consignar correctamente su dirección, referencia y número de contacto para coordinar la entrega.
        </li>
        <li class="mb-3">
            <strong>Condiciones de Pago y Crédito Comercial:</strong>
            Las compras en tienda online se procesan al contado. Para clientes corporativos y distribuidores B2B con línea de crédito aprobada, las facturas son pagaderas dentro del plazo acordado en el comprobante (21 o 30 días calendario). En caso de incumplimiento, AGRO PERUVIAN FOODS S.A.C. podrá suspender nuevos despachos hasta la regularización del saldo pendiente.
        </li>
        <li class="mb-3">
            <strong>Garantía de Calidad, Cambios y Devoluciones:</strong>
            Ofrecemos garantía de satisfacción de <strong>30 días calendario</strong> para productos que presenten defectos de fábrica o lleguen dañados durante el transporte, siempre que el envase conserve su precinto de seguridad intacto y se notifique dentro de los <strong>8 días calendario</strong> posteriores a la recepción al correo <a href="mailto:agroperuvianfoods@gmail.com">agroperuvianfoods@gmail.com</a> o al WhatsApp +51 991 215 347 adjuntando su comprobante y evidencia fotográfica.
        </li>
        <li class="mb-3">
            <strong>Protección de Datos Personales y Legislación Aplicable:</strong>
            Los datos personales proporcionados por el cliente serán tratados conforme a la Ley N.° 29733 (Ley de Protección de Datos Personales del Perú) exclusivamente para gestionar pedidos, envíos y facturación electrónica. Toda relación comercial se rige por las leyes de la República del Perú y el Código de Protección y Defensa del Consumidor (INDECOPI).
        </li>
    </ol>
</div>
""".strip()

CATALOGO: Dict[int, Dict[str, Any]] = {
    20: {"sku": "APF-ACV-30ML",  "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    21: {"sku": "APF-ACV-120ML", "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    22: {"sku": "APF-ACV-250ML", "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    23: {"sku": "APF-ACV-460ML", "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    24: {"sku": "APF-ACV-1L",    "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    25: {"sku": "APF-ACV-4L",    "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    26: {"sku": "APF-ACV-20L",   "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    27: {"sku": "APF-CGE-500G",  "derivado": "Cacao", "modalidad": "Minorista",       "tipo": "Cacao Criollo y Derivados", "tags": ["100% Orgánico"]},
    28: {"sku": "APF-CGE-1KG",   "derivado": "Cacao", "modalidad": "Minorista",       "tipo": "Cacao Criollo y Derivados", "tags": ["100% Orgánico"]},
    29: {"sku": "APF-CRD-250G",  "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Coco Rallado y Harina",     "tags": ["Sin Gluten / Keto"]},
    30: {"sku": "APF-CRD-500G",  "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Coco Rallado y Harina",     "tags": ["Sin Gluten / Keto"]},
    31: {"sku": "APF-BMY-30ML",  "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    32: {"sku": "APF-BMY-120ML", "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    33: {"sku": "APF-BMY-250ML", "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    34: {"sku": "APF-BMY-460ML", "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    35: {"sku": "APF-BMY-1L",    "derivado": "Coco",  "modalidad": "Mayorista (B2B)", "tipo": "Aceite de Coco Virgen",     "tags": ["Prensado en Frío", "Sin Gluten / Keto"]},
    79: {"sku": "APF-PPC-250G",  "derivado": "Cacao", "modalidad": "Minorista",       "tipo": "Cacao Criollo y Derivados", "tags": ["100% Orgánico", "Sin Gluten / Keto"]},
    80: {"sku": "APF-NCT-150G",  "derivado": "Cacao", "modalidad": "Minorista",       "tipo": "Cacao Criollo y Derivados", "tags": ["100% Orgánico", "Sin Gluten / Keto"]},
    81: {"sku": "APF-MCO-250G",  "derivado": "Cacao", "modalidad": "Minorista",       "tipo": "Cacao Criollo y Derivados", "tags": ["Prensado en Frío", "100% Orgánico"]},
    82: {"sku": "APF-HCO-500G",  "derivado": "Coco",  "modalidad": "Minorista",       "tipo": "Coco Rallado y Harina",     "tags": ["100% Orgánico", "Sin Gluten / Keto"]},
}


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
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    ctx = {"lang": "es_PE"}

    def kw(model: str, method: str, args: list, kwargs: dict = None):
        k = dict(kwargs or {})
        k.setdefault("context", ctx)
        return m.execute_kw(db, uid, pwd, model, method, args, k)

    # 1. Términos y Condiciones (/terms)
    kw("res.company", "write", [[1], {"terms_type": "html", "invoice_terms_html": TERMS_HTML}])
    print("[OK] Términos y condiciones actualizados en /terms.")

    # 2. Atributos no_variant para filtros en /shop
    def ensure_attr(name: str, seq: int, values: List[str]) -> Dict[str, Any]:
        found = kw("product.attribute", "search_read", [[["name", "=", name]]], {"fields": ["id"]})
        if found:
            aid = found[0]["id"]
            kw("product.attribute", "write", [[aid], {"create_variant": "no_variant", "display_type": "pills", "visibility": "visible", "sequence": seq}])
        else:
            aid = kw("product.attribute", "create", [{"name": name, "create_variant": "no_variant", "display_type": "pills", "visibility": "visible", "sequence": seq}])
        val_map = {}
        for idx, vname in enumerate(values, 1):
            vf = kw("product.attribute.value", "search_read", [[["attribute_id", "=", aid], ["name", "=", vname]]], {"fields": ["id"]})
            vid = vf[0]["id"] if vf else kw("product.attribute.value", "create", [{"attribute_id": aid, "name": vname, "sequence": idx}])
            val_map[vname] = vid
        return {"id": aid, "values": val_map}

    attr_derivado = ensure_attr("Derivado de", 1, ["Coco", "Cacao"])
    attr_modalidad = ensure_attr("Modalidad de Compra", 2, ["Minorista", "Mayorista (B2B)"])
    attr_tipo = ensure_attr("Tipo de Producto", 3, ["Aceite de Coco Virgen", "Cacao Criollo y Derivados", "Coco Rallado y Harina"])

    # 3. Etiquetas visibles en e-commerce
    tag_ids = {}
    for tname in ["Prensado en Frío", "Sin Gluten / Keto", "100% Orgánico"]:
        tf = kw("product.tag", "search_read", [[["name", "=", tname]]], {"fields": ["id"]})
        tid = tf[0]["id"] if tf else kw("product.tag", "create", [{"name": tname, "visible_on_ecommerce": True}])
        kw("product.tag", "write", [[tid], {"visible_on_ecommerce": True}])
        tag_ids[tname] = tid

    # 4. Asignar atributos, etiquetas, SKUs y términos buscables a los 20 productos
    for pid, cfg in CATALOGO.items():
        p = kw("product.template", "search_read", [[["id", "=", pid]]], {"fields": ["id", "name", "default_code", "description_sale"]})[0]
        for attr, val_name in [
            (attr_derivado, cfg["derivado"]),
            (attr_modalidad, cfg["modalidad"]),
            (attr_tipo, cfg["tipo"]),
        ]:
            aid = attr["id"]
            vid = attr["values"][val_name]
            lines = kw("product.template.attribute.line", "search", [[["product_tmpl_id", "=", pid], ["attribute_id", "=", aid]]])
            if lines:
                kw("product.template.attribute.line", "write", [lines, {"value_ids": [[6, 0, [vid]]]}])
            else:
                kw("product.template.attribute.line", "create", [{"product_tmpl_id": pid, "attribute_id": aid, "value_ids": [[6, 0, [vid]]]}])

        desc = (p.get("description_sale") or "").strip()
        meta_line = f"Derivado de {cfg['derivado']} • Venta {cfg['modalidad']}."
        if f"Derivado de {cfg['derivado']}" not in desc:
            desc = f"{desc}\n{meta_line}" if desc else meta_line

        vals: Dict[str, Any] = {
            "product_tag_ids": [[6, 0, [tag_ids[t] for t in cfg["tags"]]]],
            "description_sale": desc,
        }
        if not p.get("default_code"):
            vals["default_code"] = cfg["sku"]
        kw("product.template", "write", [[pid], vals])
        print(f"  [OK] ID {pid:>2} | {cfg['derivado']:<5} | {cfg['modalidad']:<15} | {p['name']}")

    # 5. Actualizar placeholder de búsqueda (Vista 1702)
    v1702 = kw("ir.ui.view", "read", [[1702], ["arch_db"]])[0]["arch_db"]
    new_v1702 = v1702.replace(
        '<t t-set="search_placeholder">Buscar…</t>',
        '<t t-set="search_placeholder">Buscar aceite de coco, cacao, mayorista, minorista, harina…</t>',
    )
    if new_v1702 != v1702:
        kw("ir.ui.view", "write", [[1702], {"arch_db": new_v1702}])
        print("[OK] Placeholder de búsqueda actualizado en vista 1702.")


if __name__ == "__main__":
    main()

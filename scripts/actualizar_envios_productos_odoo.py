#!/usr/bin/env python3
"""
Actualiza la información y tiempos de envío en todos los productos publicados de
AGRO PERUVIAN FOODS S.A.C. en Odoo 17:
  - Plazo de entrega al cliente (sale_delay = 2 días) en pestaña Inventario.
  - Descripción comercial de cada producto (description_sale) con política de envío.
  - Bloque global de envío en página de producto (website_sale.product_custom_text).
  - Tarjeta de envíos en la página de inicio (website.homepage).
  - Descripción del método de envío en checkout (delivery.carrier).
"""

import socket
import urllib.request
import xmlrpc.client
from pathlib import Path
from typing import Dict


SHIPPING_LINE = "Envío a Lima o provincias: 2 días máximo. Demás regiones: entre 2-7 días."


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
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    ctx = {"lang": "es_PE"}

    # 1. Actualizar todos los productos publicados en E-Commerce
    prods = m.execute_kw(
        db, uid, pwd, "product.template", "search_read",
        [[["website_published", "=", True], ["sale_ok", "=", True]]],
        {"fields": ["id", "name", "description_sale", "sale_delay"], "context": ctx},
    )
    for p in prods:
        desc = (p.get("description_sale") or "").strip()
        if "Envío a Lima o provincias" not in desc:
            new_desc = f"{desc}\n{SHIPPING_LINE}" if desc else SHIPPING_LINE
        else:
            new_desc = desc
        m.execute_kw(
            db, uid, pwd, "product.template", "write",
            [[p["id"]], {"sale_delay": 2.0, "description_sale": new_desc}],
            {"context": ctx},
        )
        print(f"  [OK] Producto ID {p['id']:>2}: {p['name']} (sale_delay=2 días)")

    # 2. Actualizar vista global de términos y envío en la ficha de producto (ID 2484)
    terms_xml = """<data inherit_id="website_sale.product" customize_show="True" active="True" name="Terms and Conditions" priority="21">
        <xpath expr="//div[@id='o_product_terms_and_share']" position="inside">
            <p class="text-muted mb-0">
                <a href="/terms" class="text-muted"><u>Términos y condiciones</u></a><br/>
                Garantía de devolución de 30 días<br/>
                <i class="fa fa-truck me-1" style="color: #2D5A27;"/><strong>Envío a Lima o provincias:</strong> 2 días máximo<br/>
                <i class="fa fa-map-marker me-1" style="color: #2D5A27;"/><strong>Demás regiones:</strong> entre 2-7 días
            </p>
        </xpath>
    </data>"""
    m.execute_kw(db, uid, pwd, "ir.ui.view", "write", [[2484], {"arch_db": terms_xml}], {"context": ctx})
    print("  [OK] Vista 2484 (website_sale.product_custom_text) actualizada.")

    # 2b. Desactivar botones de compartir (Facebook, X, Pinterest, correo) dentro de la ficha de producto
    share_views = m.execute_kw(
        db, uid, pwd, "ir.ui.view", "search",
        [[["key", "=", "website_sale.product_share_buttons"]]],
    )
    if share_views:
        m.execute_kw(db, uid, pwd, "ir.ui.view", "write", [share_views, {"active": False}])
        print(f"  [OK] Botones de compartir en producto desactivados (vistas {share_views}).")

    # 3. Actualizar tarjeta de envíos en Homepage (ID 1596)
    hp = m.execute_kw(db, uid, pwd, "ir.ui.view", "read", [[1596], ["arch_db"]], {"context": ctx})[0]["arch_db"]
    new_hp = hp.replace(
        "Atención a Lima y provincias",
        "Lima o provincias: máx. 2 días • Demás regiones: 2-7 días",
    )
    if new_hp != hp:
        m.execute_kw(db, uid, pwd, "ir.ui.view", "write", [[1596], {"arch_db": new_hp}], {"context": ctx})
        print("  [OK] Vista 1596 (website.homepage) actualizada.")

    # 4. Actualizar descripción del método de envío en Checkout
    carriers = m.execute_kw(db, uid, pwd, "delivery.carrier", "search", [[["active", "=", True]]])
    if carriers:
        m.execute_kw(
            db, uid, pwd, "delivery.carrier", "write",
            [carriers, {"website_description": SHIPPING_LINE}],
            {"context": ctx},
        )
        print(f"  [OK] Métodos de envío actualizados: {carriers}")

    # 5. Verificación en vivo
    html = urllib.request.urlopen(f"{url}/shop/22", timeout=15).read().decode("utf-8", errors="ignore")
    print("Verificación en /shop/22 -> '2 días máximo':", "2 días máximo" in html)
    print("Verificación en /shop/22 -> '2-7 días':", "2-7 días" in html)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Actualiza el Header (+51 991 215 347), Footer (datos reales + redes), Copyright y Contacto
de AGRO PERUVIAN FOODS S.A.C. en todos los idiomas activos de Odoo 17.
"""

import socket
import urllib.request
import xmlrpc.client
from pathlib import Path
from typing import Dict


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

    socket.setdefaulttimeout(25)
    uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True).authenticate(db, user, pwd, {})
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    langs = [
        l["code"]
        for l in m.execute_kw(db, uid, pwd, "res.lang", "search_read", [[["active", "=", True]]], {"fields": ["code"]})
    ]
    print("Idiomas activos en Odoo:", langs)

    footer_xml = """<data inherit_id="website.layout" name="Default" active="True">
    <xpath expr="//div[@id='footer']" position="replace">
        <div id="footer" class="oe_structure oe_structure_solo" t-ignore="true" t-if="not no_footer">
            <section class="s_text_block pt40 pb16" data-snippet="s_text_block" data-name="Text">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-2 pt24 pb24">
                            <h5 class="mb-3">Enlaces útiles</h5>
                            <ul class="list-unstyled">
                                <li><a href="/">Inicio</a></li>
                                <li><a href="/shop">Tienda Online</a></li>
                                <li><a href="/about-us">Sobre nosotros</a></li>
                                <li><a href="/privacy">Política de privacidad</a></li>
                                <li><a href="/contactus">Contacto</a></li>
                            </ul>
                        </div>
                        <div class="col-lg-5 pt24 pb24">
                            <h5 class="mb-3">AGRO PERUVIAN FOODS S.A.C.</h5>
                            <p>Transformando la riqueza del coco y cacao peruano desde noviembre de 2022. Elaboramos aceite de coco virgen prensado en frío, coco rallado, harinas sin gluten y derivados puros de cacao criollo 100% naturales.
                            <br/><br/><strong>RUC:</strong> 20609060876<br/><strong>Oficina:</strong> Asoc. Los Sauces Mz. E Lote 22, Puente Piedra, Lima - Perú.</p>
                        </div>
                        <div id="connect" class="col-lg-4 offset-lg-1 pt24 pb24">
                            <h5 class="mb-3">Contáctenos</h5>
                            <ul class="list-unstyled">
                                <li><i class="fa fa-map-marker fa-fw me-2"/><span>Puente Piedra, Lima - Perú</span></li>
                                <li><i class="fa fa-envelope fa-fw me-2"/><span><a href="mailto:agroperuvianfoods@gmail.com">agroperuvianfoods@gmail.com</a></span></li>
                                <li><i class="fa fa-phone fa-fw me-2"/><span class="o_force_ltr"><a href="tel:+51991215347">+51 991 215 347</a></span></li>
                            </ul>
                            <div class="s_social_media text-start o_not_editable" data-snippet="s_social_media" data-name="Social Media" contenteditable="false">
                                <h5 class="s_social_media_title d-none" contenteditable="true">Síganos</h5>
                                <a href="https://www.instagram.com/agroperuvianfoods/" class="s_social_media_instagram" target="_blank" aria-label="Instagram">
                                    <i class="fa fa-instagram rounded-circle shadow-sm o_editable_media"/>
                                </a>
                                <a href="https://www.facebook.com/p/Agro-Peruvian-Foods-61564506115444/" class="s_social_media_facebook" target="_blank" aria-label="Facebook">
                                    <i class="fa fa-facebook rounded-circle shadow-sm o_editable_media"/>
                                </a>
                                <a href="https://www.linkedin.com/company/agro-peruvian-foods/home/" class="s_social_media_linkedin" target="_blank" aria-label="LinkedIn">
                                    <i class="fa fa-linkedin rounded-circle shadow-sm o_editable_media"/>
                                </a>
                                <a href="https://wa.me/51991215347" class="text-800" target="_blank" aria-label="WhatsApp">
                                    <i class="fa fa-whatsapp rounded-circle shadow-sm o_editable_media"/>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </xpath>
</data>"""

    copyright_xml = """<data inherit_id="website.layout">
    <xpath expr="//footer//span[hasclass('o_footer_copyright_name')]" position="replace">
        <span class="o_footer_copyright_name me-2">Copyright &amp;copy; 2026 AGRO PERUVIAN FOODS S.A.C. &bull; RUC 20609060876</span>
    </xpath>
</data>"""

    for lg in langs:
        ctx = {"lang": lg}
        m.execute_kw(db, uid, pwd, "ir.ui.view", "write", [[2579], {"arch_db": footer_xml}], {"context": ctx})
        m.execute_kw(db, uid, pwd, "ir.ui.view", "write", [[1661], {"arch_db": copyright_xml}], {"context": ctx})

        for vid in [1716, 1589]:
            arch = m.execute_kw(db, uid, pwd, "ir.ui.view", "read", [[vid], ["arch_db"]], {"context": ctx})[0]["arch_db"]
            new_arch = (
                arch.replace("+1 555-555-5556", "+51 991 215 347")
                .replace("+1 (650) 555-0111", "+51 991 215 347")
                .replace("tel:+1 555-555-5556", "tel:+51991215347")
                .replace("info@yourcompany.example.com", "agroperuvianfoods@gmail.com")
                .replace("info@tuempresa.ejemplo.com", "agroperuvianfoods@gmail.com")
                .replace("3575 Fake Buena Vista Avenue", "Asoc. Los Sauces Mz. E Lote 22, Puente Piedra, Lima - Perú")
                .replace("My Company", "AGRO PERUVIAN FOODS S.A.C.")
                .replace("Mi empresa", "AGRO PERUVIAN FOODS S.A.C.")
            )
            if new_arch != arch:
                m.execute_kw(db, uid, pwd, "ir.ui.view", "write", [[vid], {"arch_db": new_arch}], {"context": ctx})
                print(f"  [OK] Vista {vid} ({lg}) actualizada.")

    # Verificación en vivo sobre el HTML renderizado
    html = urllib.request.urlopen(f"{url}/", timeout=15).read().decode("utf-8", errors="ignore")
    html_contact = urllib.request.urlopen(f"{url}/contactus", timeout=15).read().decode("utf-8", errors="ignore")
    print("\n--- VERIFICACIÓN EN HTML RENDERIZADO EN VIVO ---")
    print("  555-555-5556 en Home?:", "555-555-5556" in html)
    print("  tuempresa.ejemplo.com en Home?:", "tuempresa.ejemplo.com" in html)
    print("  Derechos de autor genérico en Home?:", "Derechos de autor y nombre de la empresa" in html)
    print("  agroperuvianfoods@gmail.com en Home?:", "agroperuvianfoods@gmail.com" in html)
    print("  +51 991 215 347 en Home?:", "+51 991 215 347" in html)
    print("  RUC 20609060876 en Home?:", "20609060876" in html)
    print("  555-555-5556 en Contacto?:", "555-555-5556" in html_contact)


if __name__ == "__main__":
    main()

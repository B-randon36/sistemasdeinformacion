#!/usr/bin/env python3
"""
Decoración integral del E-commerce de AGRO PERUVIAN FOODS S.A.C. en Odoo 17.
(Librería estándar de Python: xmlrpc.client, base64, pathlib)

Realiza:
  1. Actualiza datos oficiales de la compañía (RUC 20609060876, oficina Puente Piedra, correo comercial y teléfono).
  2. Configura nombre del sitio web, menús en español y enlaces oficiales de Instagram, LinkedIn y Facebook.
  3. Sube las fotografías reales (E:\\SI\\productosimagenes) y generadas de estudio a los 20 productos del E-commerce,
     además de enriquecer sus descripciones comerciales.
  4. Sube el banner hero como ir.attachment público y construye un diseño editorial profesional en Inicio (/)
     y Sobre Nosotros (/about-us) con la paleta Marrón Cacao (#3D2314) y Verde Selva (#2D5A27).
"""

import base64
import socket
import xmlrpc.client
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT_DIR / "productosimagenes"
GEN_DIR = IMG_DIR / "generated"


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


def leer_b64(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> None:
    env = cargar_env(ROOT_DIR / ".env")
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

    def q(model: str, domain: list, fields: list, limit: int = 200) -> List[dict]:
        return call(model, "search_read", [domain], {"fields": fields, "limit": limit})

    print("=" * 74)
    print("1. ACTUALIZANDO COMPAÑÍA, SITIO WEB, REDES SOCIALES Y MENÚS EN ESPAÑOL")
    print("=" * 74)

    call(
        "res.company",
        "write",
        [
            [1],
            {
                "name": "AGRO PERUVIAN FOODS S.A.C.",
                "vat": "20609060876",
                "street": "Asoc. Los Sauces Mz. E Lote 22",
                "street2": "Cerca al Río Chillón - Puente de Madera",
                "city": "Puente Piedra, Lima",
                "phone": "+51 991 215 347",
                "email": "agroperuvianfoods@gmail.com",
                "website": "http://52.86.231.75:8069",
            },
        ],
    )
    print("  [OK] res.company actualizado con RUC 20609060876, oficina Puente Piedra y agroperuvianfoods@gmail.com")

    call(
        "website",
        "write",
        [
            [1],
            {
                "name": "Agro Peruvian Foods",
                "social_instagram": "https://www.instagram.com/agroperuvianfoods/",
                "social_linkedin": "https://www.linkedin.com/company/agro-peruvian-foods/home/",
                "social_facebook": "https://www.facebook.com/p/Agro-Peruvian-Foods-61564506115444/",
            },
        ],
    )
    print("  [OK] Sitio web renombrado a 'Agro Peruvian Foods' y redes oficiales enlazadas.")

    # Traducir menús superiores al español
    renombres_menu = {
        "Home": "Inicio",
        "Shop": "Tienda",
        "Contact us": "Contacto",
    }
    for mn in q("website.menu", [], ["id", "name"]):
        if mn["name"] in renombres_menu:
            call("website.menu", "write", [[mn["id"]], {"name": renombres_menu[mn["name"]]}])
    print("  [OK] Menú principal traducido: Inicio | Tienda | Sobre nosotros | Contacto")

    print("\n" + "=" * 74)
    print("2. SUBIENDO FOTOS REALES Y DE ESTUDIO A LOS 20 PRODUCTOS DEL E-COMMERCE")
    print("=" * 74)

    mapa_productos: Dict[int, Dict[str, Any]] = {
        20: {
            "img": IMG_DIR / "aceite de coco virgen 30ml prensado en frio 5 soles infaltable 100%natural sin preservantes ni aditivos.jpeg",
            "desc": "Aceite de coco virgen prensado en frío (30 ml). Presentación infaltable de bolsillo, 100% natural, sin preservantes ni aditivos.",
        },
        21: {
            "img": IMG_DIR / "aceite de coco virgen 120ml prensado en frio 12 soles esencial 100% natural sin preservantes ni aditivos.jpeg",
            "desc": "Aceite de coco virgen prensado en frío (120 ml). Presentación esencial para cocina saludable y cuidado personal, 100% natural.",
        },
        22: {
            "img": IMG_DIR / "aceite de coco virgen 250ml prensado en frio 20 soles rutina diaria 100% natural sin preservantes ni aditivos.jpeg",
            "desc": "Aceite de coco virgen prensado en frío (250 ml). Ideal para tu rutina diaria en alimentación saludable, dieta keto y cosmética natural.",
        },
        23: {
            "img": IMG_DIR / "aceite de coco vigen 460ml prensado en frio 35 soles rinde más 100% natural sin preservante ni aditivos.jpeg",
            "desc": "Aceite de coco virgen prensado en frío (460 ml). Formato que rinde más, 100% natural, sin preservantes ni aditivos.",
        },
        24: {
            "img": IMG_DIR / "aceite de coco virgen 1L prensado en frio 65 soles familiar 100% natural sin preservantes ni aditivos.jpeg",
            "desc": "Aceite de coco virgen prensado en frío (1 Litro). Presentación familiar en frasco de vidrio con tapa precintable, 100% puro.",
        },
        25: {
            "img": IMG_DIR / "Aceite de Coco Virgen Balde de 4L 200 soles Hogares Y empredimientos 100% natural.jpeg",
            "desc": "Aceite de coco virgen en balde grado alimentario de 4 Litros. Diseñado para hogares grandes, reposterías y emprendimientos saludables.",
        },
        26: {
            "img": IMG_DIR / "Aceite de coco virgen balde de 20l 730soles Negocios y restaurantes 100% natural.jpeg",
            "desc": "Aceite de coco virgen en balde industrial de 20 Litros. Máximo rendimiento para negocios, restaurantes, hoteles y plantas procesadoras.",
        },
        27: {
            "img": IMG_DIR / "Cacao grano entero sin tostar aroma intenso 14 soles 100% natural calidad seleccionada.jpeg",
            "desc": "Cacao criollo en grano entero sin tostar (500 g). Aroma intenso, calidad seleccionada de la selva peruana, 100% natural.",
        },
        28: {
            "img": IMG_DIR / "cacao grano entero 1 kg sin tostar aroma intenso 28 soles 100% natural calidad seleccionada.jpeg",
            "desc": "Cacao criollo en grano entero sin tostar (1 kg). Ideal para chocolatería fina, tostado artesanal y consumo directo.",
        },
        29: {
            "img": IMG_DIR / "coco rallado doypack 250gr hebra larga 8 soles con grasa 100% natural excelente calidad.jpeg",
            "desc": "Coco rallado en hebra larga con grasa natural (Doypack 250 g). 100% natural sin azúcar añadida, excelente calidad para repostería.",
        },
        30: {
            "img": IMG_DIR / "coco rallado doypack 500gr hebra larga 16 soles con grasa 100% natural excelente calidad.jpeg",
            "desc": "Coco rallado en hebra larga con grasa natural (Doypack 500 g). Presentación rendidora con cierre zipper hermético.",
        },
        31: {
            "img": IMG_DIR / "Aceite de coco virrgen 30ml bandeja de 36 unidad 0 soles precios por mayor distribuidor.jpeg",
            "desc": "Bandeja Mayorista (x24 unidades) de Aceite de Coco Virgen 30 ml. Precio especial para bio tiendas, farmacias y distribuidores.",
        },
        32: {
            "img": IMG_DIR / "aceite de coco virgen 120ml bandeja de 36 unidades 0 soles precios por mayor distribuidor.jpeg",
            "desc": "Bandeja Mayorista (x24 unidades) de Aceite de Coco Virgen 120 ml. Stock conectado a Manufactura BOM para despacho rápido B2B.",
        },
        33: {
            "img": GEN_DIR / "bandeja_250ml.png",
            "desc": "Bandeja Mayorista (x12 unidades) de Aceite de Coco Virgen 250 ml. Nuestro formato más solicitado por tiendas saludables y supermercados.",
        },
        34: {
            "img": IMG_DIR / "aceite de coco virgen 460ml bandeja de 24 unidades 0 soles precios por mayor distribuidor.jpeg",
            "desc": "Bandeja Mayorista (x12 unidades) de Aceite de Coco Virgen 460 ml. Precio preferencial de distribuidor directo de fábrica.",
        },
        35: {
            "img": IMG_DIR / "aceite de coco virgen 1L bandeja de 25 unidades 0 soles precios por mayor distribuidor.jpeg",
            "desc": "Bandeja Mayorista (x6 unidades) de Aceite de Coco Virgen 1 Litro. Ideal para comercios naturistas y canal HORECA.",
        },
        79: {
            "img": GEN_DIR / "pasta_pura_cacao_250g.png",
            "desc": "Pasta pura de cacao criollo 100% orgánico (250 g). Sin azúcar añadida ni conservantes; ideal para chocolate de taza y repostería gourmet.",
        },
        80: {
            "img": GEN_DIR / "nibs_cacao_150g.png",
            "desc": "Nibs de cacao criollo tostado artesanalmente (150 g). Crujientes, ricos en antioxidantes y magnesio para bowls, smoothies y snacks.",
        },
        81: {
            "img": GEN_DIR / "manteca_cacao_250g.png",
            "desc": "Manteca de cacao orgánica prensada en frío (250 g). Pureza 100% grado alimentario y cosmético natural.",
        },
        82: {
            "img": GEN_DIR / "harina_coco_500g.png",
            "desc": "Harina de coco orgánica sin gluten (500 g). Alta en fibra, baja en carbohidratos, perfecta para dieta keto y panadería saludable.",
        },
    }

    subidas = 0
    for tmpl_id, info in mapa_productos.items():
        b64 = leer_b64(info["img"])
        vals: Dict[str, Any] = {"description_sale": info["desc"]}
        if b64:
            vals["image_1920"] = b64
            subidas += 1
        else:
            print(f"  [WARN] Imagen no encontrada para ID {tmpl_id}: {info['img']}")
        call("product.template", "write", [[tmpl_id], vals])
        print(f"  [OK] Producto ID {tmpl_id:>2} actualizado (foto={'SI' if b64 else 'NO'})")

    print(f"[OK] Total fotografías subidas a /shop: {subidas}/20")

    print("\n" + "=" * 74)
    print("3. SUBIENDO BANNER HERO Y DECORANDO INICIO (/) Y SOBRE NOSOTROS (/about-us)")
    print("=" * 74)

    # Subir Hero Banner como ir.attachment público
    hero_path = GEN_DIR / "hero_agroperuvian.png"
    hero_url = "/web/image/website.s_cover_default_image"
    hero_b64 = leer_b64(hero_path)
    if hero_b64:
        existing_att = q("ir.attachment", [["name", "=", "agroperuvian_hero_banner.png"]], ["id"])
        if existing_att:
            att_id = existing_att[0]["id"]
            call("ir.attachment", "write", [[att_id], {"datas": hero_b64, "public": True}])
        else:
            att_id = call(
                "ir.attachment",
                "create",
                [
                    {
                        "name": "agroperuvian_hero_banner.png",
                        "type": "binary",
                        "datas": hero_b64,
                        "mimetype": "image/png",
                        "public": True,
                    }
                ],
            )
        hero_url = f"/web/image/{att_id}"
        print(f"  [OK] Hero Banner subido como attachment público: {hero_url}")

    # Obtener IDs de categorías públicas para enlaces directos
    cats = {c["name"]: c["id"] for c in q("product.public.category", [], ["id", "name"])}
    cat_aceites = cats.get("Aceites de Coco Virgen", 1)
    cat_cacao = cats.get("Derivados de Cacao Orgánico", 2)
    cat_harinas = cats.get("Coco Rallado y Harinas", 3)
    cat_mayorista = cats.get("Bandejas Mayoristas B2B", 4)

    # Vista Homepage (ID 1596) - QWeb XML estrictamente válido
    home_xml = f"""<t name="Homepage" t-name="website.homepage">
  <t t-call="website.layout">
    <t t-set="pageName" t-value="'homepage'"/>
    <div id="wrap" class="oe_structure">

      <!-- HERO SECTION -->
      <section class="position-relative text-white py-5" style="background: linear-gradient(115deg, rgba(61,35,20,0.88) 0%, rgba(45,90,39,0.78) 100%), url('{hero_url}') center/cover no-repeat; min-height: 540px; display: flex; align-items: center;">
        <div class="container py-5">
          <div class="row align-items-center">
            <div class="col-lg-8">
              <span class="badge rounded-pill px-3 py-2 mb-3" style="background-color: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.35); font-size: 0.82rem; letter-spacing: 0.04em;">
                100% NATURAL &bull; PRENSADO EN FRÍO &bull; SIN PRESERVANTES
              </span>
              <h1 class="display-4 fw-bold mb-3" style="line-height: 1.15;">
                Transformando la riqueza del coco y cacao peruano
              </h1>
              <p class="lead mb-4" style="color: #f3efe9; max-width: 640px;">
                En <strong>AGRO PERUVIAN FOODS S.A.C.</strong> elaboramos aceites de coco virgen, coco rallado, harinas y derivados puros de cacao criollo con trazabilidad directa desde manufactura para hogares, bio tiendas y distribuidores en todo el Perú.
              </p>
              <div class="d-flex flex-wrap gap-3">
                <a href="/shop" class="btn btn-lg fw-bold px-4 py-3 shadow" style="background-color: #C88A2E; color: #ffffff; border: none; border-radius: 12px;">
                  <i class="fa fa-shopping-bag me-2"/>Explorar Tienda Online
                </a>
                <a href="https://wa.me/51991215347?text=Hola%20Agro%20Peruvian%20Foods,%20deseo%20informaci%C3%B3n%20sobre%20sus%20productos." target="_blank" class="btn btn-lg fw-bold px-4 py-3" style="background-color: #ffffff; color: #2D5A27; border-radius: 12px;">
                  <i class="fa fa-whatsapp me-2"/>Cotizar por WhatsApp
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- BARRA DE PROPUESTA DE VALOR -->
      <section class="py-4" style="background-color: #FAF7F2; border-bottom: 1px solid #e6dfd5;">
        <div class="container">
          <div class="row text-center g-3">
            <div class="col-6 col-md-3">
              <div class="p-2">
                <i class="fa fa-leaf fa-2x mb-2" style="color: #2D5A27;"/>
                <h6 class="fw-bold mb-1" style="color: #3D2314;">100% Natural y Puro</h6>
                <p class="small text-muted mb-0">Sin aditivos, colorantes ni preservantes</p>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-2">
                <i class="fa fa-cogs fa-2x mb-2" style="color: #2D5A27;"/>
                <h6 class="fw-bold mb-1" style="color: #3D2314;">Stock Real en Vivo</h6>
                <p class="small text-muted mb-0">Conectado directo a Manufactura BOM</p>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-2">
                <i class="fa fa-cubes fa-2x mb-2" style="color: #2D5A27;"/>
                <h6 class="fw-bold mb-1" style="color: #3D2314;">Minorista y Mayorista</h6>
                <p class="small text-muted mb-0">Desde 30 ml hasta baldes de 20 L y bandejas</p>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-2">
                <i class="fa fa-truck fa-2x mb-2" style="color: #2D5A27;"/>
                <h6 class="fw-bold mb-1" style="color: #3D2314;">Envíos a Todo el Perú</h6>
                <p class="small text-muted mb-0">Atención a Lima y provincias</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- CATEGORÍAS DE PRODUCTOS -->
      <section class="py-5 bg-white">
        <div class="container py-3">
          <div class="text-center mb-5">
            <span class="text-uppercase fw-bold small" style="color: #2D5A27; letter-spacing: 0.1em;">Nuestras Líneas</span>
            <h2 class="fw-bold mt-1" style="color: #3D2314;">Explora Nuestras Categorías Naturales</h2>
            <p class="text-muted">Productos frescos elaborados bajo estrictos estándares de calidad agroindustrial.</p>
          </div>

          <div class="row g-4">
            <div class="col-md-6 col-lg-3">
              <a href="/shop/category/{cat_aceites}" class="text-decoration-none">
                <div class="card h-100 border-0 shadow-sm overflow-hidden" style="border-radius: 16px;">
                  <img src="/web/image/product.template/22/image_512" alt="Aceites de Coco Virgen" class="card-img-top" style="height: 220px; object-fit: cover;"/>
                  <div class="card-body text-center" style="background-color: #FAF7F2;">
                    <h5 class="fw-bold mb-1" style="color: #3D2314;">Aceites de Coco Virgen</h5>
                    <p class="small text-muted mb-2">Prensados en frío: 30 ml, 120 ml, 250 ml, 460 ml, 1 L, 4 L y 20 L.</p>
                    <span class="fw-bold small" style="color: #2D5A27;">Ver productos &rarr;</span>
                  </div>
                </div>
              </a>
            </div>

            <div class="col-md-6 col-lg-3">
              <a href="/shop/category/{cat_cacao}" class="text-decoration-none">
                <div class="card h-100 border-0 shadow-sm overflow-hidden" style="border-radius: 16px;">
                  <img src="/web/image/product.template/79/image_512" alt="Derivados de Cacao Orgánico" class="card-img-top" style="height: 220px; object-fit: cover;"/>
                  <div class="card-body text-center" style="background-color: #FAF7F2;">
                    <h5 class="fw-bold mb-1" style="color: #3D2314;">Derivados de Cacao</h5>
                    <p class="small text-muted mb-2">Pasta pura 100%, nibs tostados, manteca virgen y grano entero.</p>
                    <span class="fw-bold small" style="color: #2D5A27;">Ver productos &rarr;</span>
                  </div>
                </div>
              </a>
            </div>

            <div class="col-md-6 col-lg-3">
              <a href="/shop/category/{cat_harinas}" class="text-decoration-none">
                <div class="card h-100 border-0 shadow-sm overflow-hidden" style="border-radius: 16px;">
                  <img src="/web/image/product.template/30/image_512" alt="Coco Rallado y Harinas" class="card-img-top" style="height: 220px; object-fit: cover;"/>
                  <div class="card-body text-center" style="background-color: #FAF7F2;">
                    <h5 class="fw-bold mb-1" style="color: #3D2314;">Coco Rallado y Harinas</h5>
                    <p class="small text-muted mb-2">Coco rallado hebra larga con grasa natural y harina sin gluten.</p>
                    <span class="fw-bold small" style="color: #2D5A27;">Ver productos &rarr;</span>
                  </div>
                </div>
              </a>
            </div>

            <div class="col-md-6 col-lg-3">
              <a href="/shop/category/{cat_mayorista}" class="text-decoration-none">
                <div class="card h-100 border-0 shadow-sm overflow-hidden" style="border-radius: 16px;">
                  <img src="/web/image/product.template/33/image_512" alt="Bandejas Mayoristas B2B" class="card-img-top" style="height: 220px; object-fit: cover;"/>
                  <div class="card-body text-center" style="background-color: #FAF7F2;">
                    <h5 class="fw-bold mb-1" style="color: #3D2314;">Bandejas Mayoristas B2B</h5>
                    <p class="small text-muted mb-2">Packs x6, x12 y x24 con precios preferenciales para distribuidores.</p>
                    <span class="fw-bold small" style="color: #2D5A27;">Ver productos &rarr;</span>
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>
      </section>

      <!-- PRODUCTOS DESTACADOS -->
      <section class="py-5" style="background-color: #FAF7F2;">
        <div class="container py-3">
          <div class="d-flex flex-wrap justify-content-between align-items-end mb-4">
            <div>
              <span class="text-uppercase fw-bold small" style="color: #2D5A27; letter-spacing: 0.1em;">Catálogo Seleccionado</span>
              <h2 class="fw-bold mt-1 mb-0" style="color: #3D2314;">Productos Más Solicitados</h2>
            </div>
            <a href="/shop" class="btn btn-outline-dark fw-bold mt-2" style="border-radius: 10px; border-color: #3D2314; color: #3D2314;">
              Ver los 20 productos en Tienda &rarr;
            </a>
          </div>

          <div class="row g-4">
            <div class="col-sm-6 col-lg-3">
              <div class="card h-100 border-0 shadow-sm" style="border-radius: 14px;">
                <img src="/web/image/product.template/22/image_512" alt="Aceite de Coco Virgen 250 ml" class="card-img-top" style="height: 210px; object-fit: cover; border-radius: 14px 14px 0 0;"/>
                <div class="card-body d-flex flex-column">
                  <h6 class="fw-bold" style="color: #3D2314;">Aceite de Coco Virgen 250 ml</h6>
                  <p class="small text-muted flex-grow-1">Prensado en frío, rutina diaria 100% natural.</p>
                  <div class="d-flex justify-content-between align-items-center mt-2">
                    <span class="fw-bold fs-5" style="color: #2D5A27;">S/ 20.00</span>
                    <a href="/shop" class="btn btn-sm text-white fw-bold" style="background-color: #3D2314; border-radius: 8px;">Comprar</a>
                  </div>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card h-100 border-0 shadow-sm" style="border-radius: 14px;">
                <img src="/web/image/product.template/79/image_512" alt="Pasta Pura de Cacao 100%" class="card-img-top" style="height: 210px; object-fit: cover; border-radius: 14px 14px 0 0;"/>
                <div class="card-body d-flex flex-column">
                  <h6 class="fw-bold" style="color: #3D2314;">Pasta Pura de Cacao 100% (250g)</h6>
                  <p class="small text-muted flex-grow-1">Cacao criollo peruano puro sin azúcar añadida.</p>
                  <div class="d-flex justify-content-between align-items-center mt-2">
                    <span class="fw-bold fs-5" style="color: #2D5A27;">S/ 20.00</span>
                    <a href="/shop" class="btn btn-sm text-white fw-bold" style="background-color: #3D2314; border-radius: 8px;">Comprar</a>
                  </div>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card h-100 border-0 shadow-sm" style="border-radius: 14px;">
                <img src="/web/image/product.template/25/image_512" alt="Aceite de Coco Balde 4L" class="card-img-top" style="height: 210px; object-fit: cover; border-radius: 14px 14px 0 0;"/>
                <div class="card-body d-flex flex-column">
                  <h6 class="fw-bold" style="color: #3D2314;">Aceite de Coco Virgen | Balde 4 L</h6>
                  <p class="small text-muted flex-grow-1">Ideal para hogares, pastelerías y emprendimientos.</p>
                  <div class="d-flex justify-content-between align-items-center mt-2">
                    <span class="fw-bold fs-5" style="color: #2D5A27;">S/ 200.00</span>
                    <a href="/shop" class="btn btn-sm text-white fw-bold" style="background-color: #3D2314; border-radius: 8px;">Comprar</a>
                  </div>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card h-100 border-0 shadow-sm" style="border-radius: 14px;">
                <img src="/web/image/product.template/80/image_512" alt="Nibs de Cacao Tostado" class="card-img-top" style="height: 210px; object-fit: cover; border-radius: 14px 14px 0 0;"/>
                <div class="card-body d-flex flex-column">
                  <h6 class="fw-bold" style="color: #3D2314;">Nibs de Cacao Tostado (150g)</h6>
                  <p class="small text-muted flex-grow-1">Trozos crujientes ricos en antioxidantes naturales.</p>
                  <div class="d-flex justify-content-between align-items-center mt-2">
                    <span class="fw-bold fs-5" style="color: #2D5A27;">S/ 14.00</span>
                    <a href="/shop" class="btn btn-sm text-white fw-bold" style="background-color: #3D2314; border-radius: 8px;">Comprar</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- BANNER MAYORISTAS B2B Y CONTACTO OFICIAL -->
      <section class="py-5 text-white" style="background: linear-gradient(135deg, #3D2314 0%, #2D5A27 100%);">
        <div class="container py-3">
          <div class="row align-items-center g-4">
            <div class="col-lg-7">
              <h2 class="fw-bold mb-3">¿Tienes una Bio Tienda, Restaurante o Supermercado?</h2>
              <p class="mb-4" style="color: #ede6dc;">
                Atendemos pedidos corporativos con facturación electrónica (<strong>F001 / B001</strong>), entregas programadas a nivel nacional y precios de distribuidor en bandejas mayoristas y baldes de 4 L y 20 L.
              </p>
              <div class="d-flex flex-wrap gap-3">
                <a href="/contactus" class="btn btn-light fw-bold px-4 py-2" style="color: #3D2314; border-radius: 10px;">
                  Solicitar Cotización B2B
                </a>
                <a href="/about-us" class="btn btn-outline-light fw-bold px-4 py-2" style="border-radius: 10px;">
                  Conoce Nuestra Empresa
                </a>
              </div>
            </div>
            <div class="col-lg-5">
              <div class="p-4" style="background-color: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.22); border-radius: 16px;">
                <h5 class="fw-bold mb-3">AGRO PERUVIAN FOODS S.A.C.</h5>
                <p class="small mb-2"><i class="fa fa-id-card me-2"/><strong>RUC:</strong> 20609060876</p>
                <p class="small mb-2"><i class="fa fa-map-marker me-2"/><strong>Oficina:</strong> Asoc. Los Sauces Mz. E Lote 22, Puente Piedra, Lima - Perú</p>
                <p class="small mb-2"><i class="fa fa-phone me-2"/><strong>Teléfono / WhatsApp:</strong> +51 991 215 347</p>
                <p class="small mb-3"><i class="fa fa-envelope me-2"/><strong>Correo:</strong> agroperuvianfoods@gmail.com</p>
                <div class="d-flex gap-3 pt-2 border-top border-light border-opacity-25">
                  <a href="https://www.instagram.com/agroperuvianfoods/" target="_blank" class="text-white text-decoration-none small fw-bold">
                    <i class="fa fa-instagram me-1"/>Instagram
                  </a>
                  <a href="https://www.facebook.com/p/Agro-Peruvian-Foods-61564506115444/" target="_blank" class="text-white text-decoration-none small fw-bold">
                    <i class="fa fa-facebook me-1"/>Facebook
                  </a>
                  <a href="https://www.linkedin.com/company/agro-peruvian-foods/home/" target="_blank" class="text-white text-decoration-none small fw-bold">
                    <i class="fa fa-linkedin me-1"/>LinkedIn
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </t>
</t>"""

    call("ir.ui.view", "write", [[1596], {"arch_db": home_xml}])
    print("  [OK] Página de Inicio (/) decorada con diseño corporativo y fotos reales.")

    # Vista Sobre Nosotros (ID 2622)
    about_xml = f"""<t name="About Us" t-name="website.sobre-nosotros">
  <t t-call="website.layout">
    <div id="wrap" class="oe_structure">

      <section class="py-5 text-white text-center" style="background: linear-gradient(120deg, rgba(61,35,20,0.92), rgba(45,90,39,0.86)), url('{hero_url}') center/cover no-repeat;">
        <div class="container py-4">
          <span class="badge rounded-pill px-3 py-2 mb-3" style="background-color: rgba(255,255,255,0.18);">SOBRE NOSOTROS</span>
          <h1 class="display-5 fw-bold mb-2">AGRO PERUVIAN FOODS S.A.C.</h1>
          <p class="lead mb-0" style="color: #f3efe9;">Transformando la riqueza del cacao y coco peruano desde noviembre de 2022</p>
        </div>
      </section>

      <section class="py-5 bg-white">
        <div class="container py-3">
          <div class="row align-items-center g-5">
            <div class="col-lg-6">
              <span class="text-uppercase fw-bold small" style="color: #2D5A27; letter-spacing: 0.08em;">Quiénes Somos</span>
              <h2 class="fw-bold mt-1 mb-3" style="color: #3D2314;">Superalimentos Peruanos con Pureza y Trazabilidad</h2>
              <p class="text-muted">
                <strong>AGRO PERUVIAN FOODS S.A.C.</strong> (RUC <strong>20609060876</strong>) es una empresa peruana dedicada a la transformación y comercialización de derivados naturales del <strong>coco</strong> y del <strong>cacao criollo</strong>.
              </p>
              <p class="text-muted">
                Trabajamos con materia prima seleccionada para ofrecer aceite de coco virgen prensado en frío, coco rallado de hebra larga, harina de coco sin gluten, granos de cacao, pasta pura 100%, nibs tostados y manteca de cacao, atendiendo tanto a consumidores finales como a bio tiendas, restaurantes y supermercados a nivel nacional.
              </p>
              <div class="row g-3 mt-3">
                <div class="col-6">
                  <div class="p-3 rounded-3" style="background-color: #FAF7F2; border-left: 4px solid #2D5A27;">
                    <h6 class="fw-bold mb-1" style="color: #3D2314;">Misión</h6>
                    <p class="small text-muted mb-0">Llevar derivados puros de coco y cacao peruano con altos estándares de inocuidad y trazabilidad a cada hogar y negocio.</p>
                  </div>
                </div>
                <div class="col-6">
                  <div class="p-3 rounded-3" style="background-color: #FAF7F2; border-left: 4px solid #C88A2E;">
                    <h6 class="fw-bold mb-1" style="color: #3D2314;">Visión</h6>
                    <p class="small text-muted mb-0">Consolidarnos como referente nacional en superalimentos naturales derivados del coco y cacao, integrando tecnología ERP y gestión sostenible.</p>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-lg-6">
              <div class="p-4 rounded-4 shadow-sm" style="background-color: #FAF7F2; border: 1px solid #e6dfd5;">
                <h4 class="fw-bold mb-3" style="color: #3D2314;">Información Corporativa Oficial</h4>
                <ul class="list-unstyled mb-4">
                  <li class="mb-2"><i class="fa fa-building me-2" style="color: #2D5A27;"/><strong>Razón Social:</strong> AGRO PERUVIAN FOODS S.A.C.</li>
                  <li class="mb-2"><i class="fa fa-id-card me-2" style="color: #2D5A27;"/><strong>RUC:</strong> 20609060876</li>
                  <li class="mb-2"><i class="fa fa-calendar me-2" style="color: #2D5A27;"/><strong>Inicio de Actividades:</strong> 16 de noviembre de 2022</li>
                  <li class="mb-2"><i class="fa fa-map-marker me-2" style="color: #2D5A27;"/><strong>Oficina:</strong> Asoc. Los Sauces Mz. E Lote 22, Puente Piedra, Lima - Perú</li>
                  <li class="mb-2"><i class="fa fa-phone me-2" style="color: #2D5A27;"/><strong>Teléfono / WhatsApp:</strong> +51 991 215 347</li>
                  <li class="mb-2"><i class="fa fa-envelope me-2" style="color: #2D5A27;"/><strong>Correo Comercial:</strong> agroperuvianfoods@gmail.com</li>
                </ul>
                <div class="d-flex flex-wrap gap-2">
                  <a href="https://www.instagram.com/agroperuvianfoods/" target="_blank" class="btn btn-sm text-white fw-bold" style="background-color: #3D2314; border-radius: 8px;">
                    <i class="fa fa-instagram me-1"/>Instagram
                  </a>
                  <a href="https://www.facebook.com/p/Agro-Peruvian-Foods-61564506115444/" target="_blank" class="btn btn-sm text-white fw-bold" style="background-color: #2D5A27; border-radius: 8px;">
                    <i class="fa fa-facebook me-1"/>Facebook
                  </a>
                  <a href="https://www.linkedin.com/company/agro-peruvian-foods/home/" target="_blank" class="btn btn-sm text-white fw-bold" style="background-color: #0a66c2; border-radius: 8px;">
                    <i class="fa fa-linkedin me-1"/>LinkedIn
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </t>
</t>"""

    call("ir.ui.view", "write", [[2622], {"arch_db": about_xml}])
    print("  [OK] Página 'Sobre nosotros' (/about-us) actualizada con historia y datos oficiales.")
    print("\n[COMPLETADO] E-commerce 100% decorado y listo en http://52.86.231.75:8069 y /shop")


if __name__ == "__main__":
    main()

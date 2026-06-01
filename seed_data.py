#!/usr/bin/env python3
"""
seed_data.py — Carga datos de prueba en Odoo 17 via XML-RPC
Ejecutar: python3 seed_data.py
"""

import sys
import getpass
import xmlrpc.client


# ── Lectura de .env ────────────────────────────────────────────────────────────

def load_env(path=".env"):
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env


def get_config():
    env = load_env()

    print("═" * 54)
    print("   Odoo 17 — Seed de datos de prueba (farmacia)")
    print("═" * 54)
    print("  Presiona Enter para aceptar el valor entre [ ].\n")

    url = (
        env.get("ODOO_URL")
        or input("  URL de Odoo [http://localhost:8069]: ").strip()
        or "http://localhost:8069"
    )
    db = (
        env.get("ODOO_DB")
        or env.get("POSTGRES_DB")
        or input("  Base de datos [farmacia_db]: ").strip()
        or "farmacia_db"
    )
    user = (
        env.get("ODOO_USER")
        or input("  Usuario admin [admin]: ").strip()
        or "admin"
    )
    password = env.get("ODOO_PASSWORD") or getpass.getpass("  Contraseña: ")

    print()
    return url.rstrip("/"), db, user, password


# ── Conexión XML-RPC ───────────────────────────────────────────────────────────

def connect(url, db, username, password):
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
    except Exception as e:
        print(f"✗ No se pudo conectar a {url}: {e}")
        sys.exit(1)

    if not uid:
        print("✗ Autenticación fallida. Verifica usuario y contraseña.")
        sys.exit(1)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    print(f"✓ Conectado como '{username}' (UID {uid}) en '{db}'\n")
    return uid, models


# ── Helpers ────────────────────────────────────────────────────────────────────

def exe(models, db, uid, password, model, method, args, kwargs=None):
    return models.execute_kw(db, uid, password, model, method, args, kwargs or {})


def search_one(models, db, uid, password, model, domain):
    ids = exe(models, db, uid, password, model, "search", [domain], {"limit": 1})
    return ids[0] if ids else None


def create_or_skip(models, db, uid, password, model, domain, values, label):
    """Crea el registro si no existe. Retorna (id, creado: bool)."""
    existing = search_one(models, db, uid, password, model, domain)
    if existing:
        print(f"  · Omitido  : {label}")
        return existing, False
    try:
        new_id = exe(models, db, uid, password, model, "create", [values])
        print(f"  ✓ Creado   : {label}")
        return new_id, True
    except Exception as e:
        print(f"  ✗ Error    : {label} → {e}")
        return None, False


# ── Datos ──────────────────────────────────────────────────────────────────────

CATEGORIES = [
    "Antibióticos",
    "Analgésicos",
    "Gastrointestinal",
    "Diabetes",
    "Antialérgicos",
    "Cardiovascular",
    "Vitaminas",
]

PRODUCTS = [
    {"name": "Amoxicilina 500mg",   "ref": "FAR-001", "price": 5.99,  "cost": 3.20,  "cat": "Antibióticos"},
    {"name": "Ibuprofeno 400mg",    "ref": "FAR-002", "price": 2.50,  "cost": 1.10,  "cat": "Analgésicos"},
    {"name": "Omeprazol 20mg",      "ref": "FAR-003", "price": 3.75,  "cost": 1.80,  "cat": "Gastrointestinal"},
    {"name": "Metformina 850mg",    "ref": "FAR-004", "price": 4.20,  "cost": 2.00,  "cat": "Diabetes"},
    {"name": "Loratadina 10mg",     "ref": "FAR-005", "price": 1.99,  "cost": 0.90,  "cat": "Antialérgicos"},
    {"name": "Atorvastatina 20mg",  "ref": "FAR-006", "price": 6.50,  "cost": 3.50,  "cat": "Cardiovascular"},
    {"name": "Paracetamol 500mg",   "ref": "FAR-007", "price": 1.25,  "cost": 0.55,  "cat": "Analgésicos"},
    {"name": "Azitromicina 500mg",  "ref": "FAR-008", "price": 8.99,  "cost": 4.80,  "cat": "Antibióticos"},
    {"name": "Vitamina C 1000mg",   "ref": "FAR-009", "price": 3.25,  "cost": 1.40,  "cat": "Vitaminas"},
    {"name": "Insulina Glargina",   "ref": "FAR-010", "price": 22.50, "cost": 14.00, "cat": "Diabetes"},
]

PARTNERS = [
    {"name": "Clínica San Rafael",         "vat": "0614-010101-101-1", "city": "San Salvador"},
    {"name": "Farmacia Central",           "vat": "0614-020202-202-2", "city": "San Salvador"},
    {"name": "Hospital Nacional Rosales",  "vat": "0614-030303-303-3", "city": "San Salvador"},
    {"name": "Droguería San Miguel",       "vat": "0614-040404-404-4", "city": "San Miguel"},
    {"name": "Clínica Santa Ana",          "vat": "0614-050505-505-5", "city": "Santa Ana"},
]

STOCK = {
    "FAR-001": 150, "FAR-002": 200, "FAR-003": 120, "FAR-004": 90,
    "FAR-005": 180, "FAR-006": 75,  "FAR-007": 300, "FAR-008": 60,
    "FAR-009": 250, "FAR-010": 40,
}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    url, db, username, password = get_config()
    uid, models = connect(url, db, username, password)

    # Wrapper con credenciales ya inyectadas
    def do(model, method, args, kwargs=None):
        return exe(models, db, uid, password, model, method, args, kwargs or {})

    def find(model, domain):
        return search_one(models, db, uid, password, model, domain)

    def upsert(model, domain, values, label):
        return create_or_skip(models, db, uid, password, model, domain, values, label)

    stats = {"created": 0, "skipped": 0, "errors": 0}

    def track(record_id, created):
        if record_id is None:
            stats["errors"] += 1
        elif created:
            stats["created"] += 1
        else:
            stats["skipped"] += 1

    # ── 1. Categorías de productos ─────────────────────────────────────────────
    print("── 1. Categorías de productos ──────────────────────")

    parent_id = find("product.category", [["name", "=", "All"]])

    cat_ids = {}
    for name in CATEGORIES:
        cat_id, created = upsert(
            "product.category",
            [["name", "=", name]],
            {"name": name, "parent_id": parent_id},
            name,
        )
        cat_ids[name] = cat_id
        track(cat_id, created)

    # ── 2. Productos farmacéuticos ─────────────────────────────────────────────
    print("\n── 2. Productos farmacéuticos ──────────────────────")

    uom_id = (
        find("uom.uom", [["name", "ilike", "Unidad"]]) or
        find("uom.uom", [["name", "ilike", "Unit"]])
    )
    if not uom_id:
        print("  ! Aviso: unidad de medida no encontrada, se usará la predeterminada.")

    prod_variant_ids = {}  # ref → product.product.id (para stock)

    for p in PRODUCTS:
        values = {
            "name":           p["name"],
            "default_code":   p["ref"],
            "list_price":     p["price"],
            "standard_price": p["cost"],
            "detailed_type":  "product",   # storable en Odoo 16+
            "type":           "product",   # compatibilidad Odoo 15
            "categ_id":       cat_ids.get(p["cat"]),
        }
        if uom_id:
            values["uom_id"]    = uom_id
            values["uom_po_id"] = uom_id

        tmpl_id, created = upsert(
            "product.template",
            [["default_code", "=", p["ref"]]],
            values,
            f"{p['name']} ({p['ref']})",
        )
        track(tmpl_id, created)

        if tmpl_id:
            variants = do("product.product", "search",
                          [[["product_tmpl_id", "=", tmpl_id]]])
            if variants:
                prod_variant_ids[p["ref"]] = variants[0]

                # Si el producto ya existía, actualizar el costo igualmente
                if not created:
                    try:
                        do("product.product", "write",
                           [[variants[0]], {"standard_price": p["cost"]}])
                    except Exception:
                        pass

    # ── 3. Clientes ────────────────────────────────────────────────────────────
    print("\n── 3. Clientes ─────────────────────────────────────")

    country_id = find("res.country", [["code", "=", "SV"]])
    if not country_id:
        print("  ! Aviso: país El Salvador (SV) no encontrado.")

    for partner in PARTNERS:
        values = {
            "name":          partner["name"],
            "vat":           partner["vat"],
            "city":          partner["city"],
            "customer_rank": 1,
            "is_company":    True,
        }
        if country_id:
            values["country_id"] = country_id

        pid, created = upsert(
            "res.partner",
            [["name", "=", partner["name"]]],
            values,
            partner["name"],
        )
        track(pid, created)

    # ── 4. Stock inicial ───────────────────────────────────────────────────────
    print("\n── 4. Stock inicial (WH/Stock) ─────────────────────")

    location_id = (
        find("stock.location", [["name", "=", "Stock"],
                                 ["usage", "=", "internal"]]) or
        find("stock.location", [["usage", "=", "internal"],
                                 ["active", "=", True]])
    )

    if not location_id:
        print("  ✗ Ubicación WH/Stock no encontrada. ¿Está instalado Inventario?")
        for _ in STOCK:
            stats["errors"] += 1
    else:
        quant_ids_to_apply = []

        for ref, qty in STOCK.items():
            prod_id = prod_variant_ids.get(ref)
            if not prod_id:
                print(f"  ✗ Variante de {ref} no disponible, saltando stock.")
                stats["errors"] += 1
                continue

            existing_quant = find(
                "stock.quant",
                [["product_id", "=", prod_id], ["location_id", "=", location_id]],
            )

            try:
                if existing_quant:
                    do("stock.quant", "write",
                       [[existing_quant], {"inventory_quantity": qty}])
                    quant_ids_to_apply.append(existing_quant)
                    print(f"  · Omitido  : {ref} (actualizado a {qty} u.)")
                    stats["skipped"] += 1
                else:
                    new_id = do("stock.quant", "create", [{
                        "product_id":           prod_id,
                        "location_id":          location_id,
                        "inventory_quantity":   qty,
                    }])
                    quant_ids_to_apply.append(new_id)
                    print(f"  ✓ Creado   : {ref} → {qty} u.")
                    stats["created"] += 1
            except Exception as e:
                print(f"  ✗ Error    : stock {ref} → {e}")
                stats["errors"] += 1

        if quant_ids_to_apply:
            try:
                do("stock.quant", "action_apply_inventory", [quant_ids_to_apply])
                print(f"\n  ✓ Ajuste de inventario aplicado ({len(quant_ids_to_apply)} productos)")
            except Exception as e:
                print(f"\n  ✗ Error al aplicar inventario: {e}")

    # ── Resumen ────────────────────────────────────────────────────────────────
    total = stats["created"] + stats["skipped"] + stats["errors"]
    print(f"""
═══════════════════════════════════════════════
  Resumen final
───────────────────────────────────────────────
  Total procesados  : {total}
  ✓ Creados         : {stats['created']}
  · Omitidos        : {stats['skipped']}
  ✗ Errores         : {stats['errors']}
═══════════════════════════════════════════════""")

    if stats["errors"] == 0:
        print("  Estado: TODO OK\n")
    else:
        print(f"  Estado: {stats['errors']} registro(s) fallaron\n")


if __name__ == "__main__":
    main()

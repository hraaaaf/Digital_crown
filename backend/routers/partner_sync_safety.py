from collections import defaultdict

from backend import models


def install_partner_sync_identity_guard(partner_sync_module) -> None:
    """Durcit P9 sans modifier le moteur canonique : aucune identité locale ambiguë.

    Le CRUD catalogue historique n'impose pas encore d'unicité SQL sur SKU/externalProductId.
    Une synchronisation API ne doit donc jamais choisir arbitrairement une ligne locale quand
    deux produits du même fournisseur partagent la même identité canonique.
    """
    if getattr(partner_sync_module, "_local_identity_guard_installed", False):
        return

    original_apply_snapshot = partner_sync_module._apply_snapshot

    def guarded_apply_snapshot(db, supplier, products):
        existing = (
            db.query(models.PartnerCatalogProduct)
            .filter(
                models.PartnerCatalogProduct.employer_id == supplier.employer_id,
                models.PartnerCatalogProduct.supplier_id == supplier.id,
            )
            .all()
        )
        by_sku = defaultdict(list)
        by_external = defaultdict(list)
        for item in existing:
            sku = str(item.sku or "").strip().casefold()
            if sku:
                by_sku[sku].append(item.id)
            external = str(item.external_product_id or "").strip().casefold()
            if external:
                by_external[external].append(item.id)

        duplicate_skus = sorted(key for key, ids in by_sku.items() if len(ids) > 1)
        duplicate_external = sorted(key for key, ids in by_external.items() if len(ids) > 1)
        if duplicate_skus or duplicate_external:
            details = []
            if duplicate_skus:
                details.append(f"SKU locaux dupliques: {', '.join(duplicate_skus[:10])}")
            if duplicate_external:
                details.append(f"externalProductId locaux dupliques: {', '.join(duplicate_external[:10])}")
            raise partner_sync_module.SupplierSyncError(
                "LOCAL_IDENTITY_AMBIGUITY",
                " ; ".join(details),
                http_status=409,
            )

        return original_apply_snapshot(db, supplier, products)

    partner_sync_module._apply_snapshot = guarded_apply_snapshot
    partner_sync_module._local_identity_guard_installed = True

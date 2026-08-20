"""Governed Level-2 to Broad Product Category taxonomy.

This module is the single executable source for mapping version 1.0.0.  The
published CSV is generated from these records; analytical data is never edited
by hand to add the grouping.
"""

from __future__ import annotations

import pandas as pd


MAPPING_VERSION = "1.0.0"

MAPPING_ROWS = (
    ("Automotive", "Automotive", "Distinct vehicle-related merchandise domain."),
    ("Baby & Toys", "Baby & Kids", "Child- and baby-oriented merchandise grouped for dashboard readability."),
    ("Cameras & Drones", "Mobile & Technology", "Consumer imaging devices and connected hardware."),
    ("Computer & Accessories", "Mobile & Technology", "Computing devices and supporting accessories."),
    ("Fashion Accessories", "Fashion", "Wearable accessories belong to the apparel and personal-style domain."),
    ("Games, Books & Hobbies", "Entertainment & Hobbies", "Source category already combines leisure media and hobby products."),
    ("Gaming & Consoles", "Mobile & Technology", "Gaming hardware and its device ecosystem; kept separate from mixed hobby media at Level 2."),
    ("Groceries & Pets", "Groceries & Pets", "Source Level-2 value already combines grocery and pet products; it cannot be split safely."),
    ("Health & Beauty", "Health & Beauty", "Distinct personal-care and wellness merchandise domain."),
    ("Home & Living", "Home", "Household living products."),
    ("Home Appliances", "Home", "Household appliances."),
    ("Men Clothes", "Fashion", "Apparel and personal-style merchandise."),
    ("Men Shoes", "Fashion", "Footwear and personal-style merchandise."),
    ("Men's Bags & Wallets", "Fashion", "Wearable and personal-style accessories."),
    ("Mobile & Accessories", "Mobile & Technology", "Mobile devices and supporting accessories."),
    ("Muslim Fashion", "Fashion", "Apparel and personal-style merchandise; source distinction remains available at Level 2."),
    ("Others", "Others", "Unclassified source category retained without invented reassignment."),
    ("Sports & Outdoor", "Sports & Outdoor", "Distinct activity and outdoor merchandise domain."),
    ("Tickets & Vouchers", "Tickets & Vouchers", "Non-physical and heterogeneous entitlement products remain separate."),
    ("Travel & Luggage", "Travel", "Travel-oriented luggage and accessories."),
    ("Watches", "Fashion", "Wearable personal accessory; retained as its original Level-2 detail."),
    ("Women Clothes", "Fashion", "Apparel and personal-style merchandise."),
    ("Women Shoes", "Fashion", "Footwear and personal-style merchandise."),
    ("Women's Bags", "Fashion", "Wearable and personal-style accessories."),
)


def mapping_frame() -> pd.DataFrame:
    """Return the deterministic governed mapping in stable Level-2 order."""
    frame = pd.DataFrame(
        MAPPING_ROWS,
        columns=["category_level_2", "broad_product_category", "mapping_reason"],
    )
    frame["mapping_version"] = MAPPING_VERSION
    return frame.sort_values("category_level_2").reset_index(drop=True)


def mapping_dict() -> dict[str, str]:
    """Return the one-to-one Level-2 lookup after structural validation."""
    frame = mapping_frame()
    if frame["category_level_2"].duplicated().any() or frame["broad_product_category"].isna().any():
        raise RuntimeError("Broad Product Category mapping is not one-to-one and complete")
    return frame.set_index("category_level_2")["broad_product_category"].to_dict()

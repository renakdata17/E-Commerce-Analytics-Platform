"""Background jobs mirroring transactional side-effects."""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

LOGGER = logging.getLogger(__name__)


@shared_task(name="merchant.send_order_receipt")
def send_order_receipt_stub(order_summary: dict[str, Any]) -> bool:
    """Stand-in email provider — swaps for SendGrid/SES in prod."""

    LOGGER.info("receipt stub :: order=%s", order_summary.get("order_id"))
    return True


@shared_task(name="merchant.restock_escalation")
def maybe_escalate_restock(sku: str, qty_on_hand: int, reorder_point: int) -> dict[str, int]:
    """Ops workflow hook invoked when SKU crosses reorder threshold."""

    if qty_on_hand > reorder_point:
        return {"skipped": 1}

    LOGGER.warning("restock recommended :: sku=%s qty=%s rop=%s", sku, qty_on_hand, reorder_point)
    return {"escalated": 1}

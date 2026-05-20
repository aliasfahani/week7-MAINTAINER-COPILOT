from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.infra.db import get_db
from app.routes.dependencies import require_admin
from app.schemas import WidgetConfigIn, WidgetConfigPatch
from app.services.widget_service import (
    create_widget_config,
    get_public_widget_config,
    list_widget_configs,
    update_widget_config,
)

router = APIRouter(tags=["widgets"])


@router.get("/widgets/{widget_id}/config")
def public_widget_config(
    widget_id: str,
    db: Session = Depends(get_db),
    origin: str | None = Header(default=None),
    referer: str | None = Header(default=None),
):
    config = get_public_widget_config(db, widget_id, origin or referer)
    if not config:
        raise HTTPException(status_code=403, detail="Widget origin is not allowed or widget does not exist")
    return config


@router.get("/widget.js")
def widget_loader() -> Response:
    widget_url = get_settings().widget_url.rstrip("/")
    script = f"""
(function(){{
  var script = document.currentScript;
  var widgetId = script && script.getAttribute('data-widget-id') || 'demo-widget';
  var iframe = document.createElement('iframe');
  iframe.src = '{widget_url}?widget_id=' + encodeURIComponent(widgetId);
  iframe.style.position = 'fixed';
  iframe.style.right = '16px';
  iframe.style.bottom = '16px';
  iframe.style.width = '380px';
  iframe.style.height = '620px';
  iframe.style.border = '0';
  iframe.style.zIndex = '2147483647';
  iframe.setAttribute('title', 'Maintainer Copilot');
  document.body.appendChild(iframe);
}})();
"""
    return Response(script, media_type="application/javascript")


@router.post("/admin/widgets")
def create_admin_widget(payload: WidgetConfigIn, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = create_widget_config(db, payload.model_dump(), created_by=admin.id)
    return {"widget_id": row.widget_id}


@router.get("/admin/widgets")
def list_admin_widgets(admin=Depends(require_admin), db: Session = Depends(get_db)):
    return {"widgets": list_widget_configs(db)}


@router.patch("/admin/widgets/{widget_id}")
def patch_admin_widget(
    widget_id: str,
    payload: WidgetConfigPatch,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = update_widget_config(db, widget_id, payload.model_dump(exclude_unset=True))
    if not row:
        raise HTTPException(status_code=404, detail="Widget not found")
    return {"widget_id": row.widget_id}

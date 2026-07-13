"""Asset topology + active-attack helpers for AI Workbench Phase 3."""

from __future__ import annotations

from typing import Any, Optional


def _node_id(asset_type: str, asset_id: int) -> str:
    return f"{asset_type.lower()}:{asset_id}"


def _resolve_lock_node(lock) -> Optional[dict]:
    mapping = [
        ("ip_asset", "ip", "IP"),
        ("subdomain_asset", "subdomain", "SUBDOMAIN"),
        ("url_asset", "url", "URL"),
        ("endpoint_asset", "endpoint", "ENDPOINT"),
        ("port_asset", "port", "PORT"),
    ]
    for fk, type_key, _ in mapping:
        obj = getattr(lock, fk, None)
        if obj is not None:
            return {
                "node_id": _node_id(type_key, obj.id),
                "asset_type": type_key,
                "asset_id": obj.id,
                "thread_id": lock.thread_id,
                "agent_role": lock.agent_role,
                "source": "asset_lock",
            }
    return None


def get_active_attacks(target_id: int) -> list[dict]:
    """Prefer AssetLock(HELD); fallback WalkCursor on active plans."""
    from apps.core.models import AssetLock, AttackPlan, WalkCursor

    active: list[dict] = []
    locks = (
        AssetLock.objects.filter(target_id=target_id, lock_status="HELD")
        .select_related(
            "ip_asset",
            "subdomain_asset",
            "url_asset",
            "endpoint_asset",
            "port_asset",
            "thread",
        )[:20]
    )
    for lock in locks:
        resolved = _resolve_lock_node(lock)
        if resolved:
            active.append(resolved)

    if active:
        return active

    # WalkCursor fallback
    plans = AttackPlan.objects.filter(target_id=target_id, status="ACTIVE")
    for plan in plans:
        cursor = (
            WalkCursor.objects.filter(plan=plan)
            .select_related(
                "current_asset_link",
                "current_asset_link__ip_asset",
                "current_asset_link__subdomain_asset",
                "current_asset_link__url_asset",
                "current_asset_link__endpoint_asset",
                "current_asset_link__port_asset",
            )
            .first()
        )
        if not cursor or not cursor.current_asset_link:
            continue
        link = cursor.current_asset_link
        for fk, type_key in [
            ("ip_asset", "ip"),
            ("subdomain_asset", "subdomain"),
            ("url_asset", "url"),
            ("endpoint_asset", "endpoint"),
            ("port_asset", "port"),
        ]:
            obj = getattr(link, fk, None)
            if obj is not None:
                active.append(
                    {
                        "node_id": _node_id(type_key, obj.id),
                        "asset_type": type_key,
                        "asset_id": obj.id,
                        "thread_id": link.agent_thread_id,
                        "agent_role": link.agent_role,
                        "source": "walk_cursor",
                    }
                )
                break
    return active


def build_target_topology(target_id: int, limits: Optional[dict] = None) -> dict:
    """
    Build nodes + edges for a target.

    Edge sources:
      1. AssetEdge rows (primary)
      2. Inferred M2M (Subdomain↔IP, Subdomain↔URL, Target→Seed/Subdomain, Vuln→asset)
    """
    from apps.core.models import (
        AssetEdge,
        IP,
        Port,
        Seed,
        Subdomain,
        Target,
        Vulnerability,
    )
    from apps.core.models.url_assets import URLResult

    limits = limits or {}
    max_sub = limits.get("subdomains", 80)
    max_ip = limits.get("ips", 80)
    max_url = limits.get("urls", 60)
    max_vuln = limits.get("vulnerabilities", 40)
    max_port = limits.get("ports", 40)

    try:
        target = Target.objects.get(pk=target_id)
    except Target.DoesNotExist:
        return None

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    edge_keys: set[str] = set()

    def add_node(nid: str, ntype: str, label: str, asset_id: Optional[int] = None, meta: Optional[dict] = None):
        if nid not in nodes:
            nodes[nid] = {
                "id": nid,
                "type": ntype,
                "label": label[:120],
                "asset_id": asset_id,
                "meta": meta or {},
                "is_active_attack": False,
            }

    def add_edge(source: str, target: str, edge_type: str, source_kind: str = "inferred"):
        if source not in nodes or target not in nodes:
            return
        key = f"{source}|{target}|{edge_type}"
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append(
            {
                "id": key,
                "source": source,
                "target": target,
                "edge_type": edge_type,
                "source_kind": source_kind,
            }
        )

    target_nid = _node_id("target", target.id)
    add_node(target_nid, "target", target.name, target.id)

    # Seeds
    for seed in Seed.objects.filter(target_id=target_id)[:30]:
        nid = _node_id("seed", seed.id)
        add_node(nid, "seed", f"{seed.type}:{seed.value}", seed.id, {"type": seed.type})
        add_edge(target_nid, nid, "HOSTS")

    # Subdomains
    subdomains = list(
        Subdomain.objects.filter(target_id=target_id).prefetch_related("ips")[:max_sub]
    )
    for sd in subdomains:
        nid = _node_id("subdomain", sd.id)
        add_node(
            nid,
            "subdomain",
            sd.name,
            sd.id,
            {"is_active": sd.is_active, "is_cdn": sd.is_cdn},
        )
        add_edge(target_nid, nid, "HOSTS")

    # IPs
    ips = list(IP.objects.filter(target_id=target_id)[:max_ip])
    for ip in ips:
        nid = _node_id("ip", ip.id)
        label = getattr(ip, "address", None) or str(ip.id)
        add_node(nid, "ip", label, ip.id)
        add_edge(target_nid, nid, "HOSTS")

    # Subdomain ↔ IP M2M
    for sd in subdomains:
        sd_nid = _node_id("subdomain", sd.id)
        for ip in sd.ips.all()[:10]:
            ip_nid = _node_id("ip", ip.id)
            if ip_nid not in nodes:
                add_node(ip_nid, "ip", getattr(ip, "address", str(ip.id)), ip.id)
            add_edge(sd_nid, ip_nid, "RESOLVES_TO")

    # Ports
    for port in Port.objects.filter(ip__target_id=target_id).select_related("ip")[:max_port]:
        pid = _node_id("port", port.id)
        label = f"{getattr(port.ip, 'address', '?')}:{port.port_number}"
        add_node(
            pid,
            "port",
            label,
            port.id,
            {"service": getattr(port, "service_name", "") or ""},
        )
        if port.ip_id:
            add_edge(_node_id("ip", port.ip_id), pid, "HOSTS")

    # URLs
    urls = list(
        URLResult.objects.filter(target_id=target_id)
        .prefetch_related("related_subdomains")[:max_url]
    )
    for url in urls:
        nid = _node_id("url", url.id)
        add_node(nid, "url", url.url or f"url#{url.id}", url.id, {"status_code": url.status_code})
        linked = False
        for sd in url.related_subdomains.all()[:5]:
            sd_nid = _node_id("subdomain", sd.id)
            if sd_nid in nodes:
                add_edge(sd_nid, nid, "LINKS_TO")
                linked = True
        if not linked:
            add_edge(target_nid, nid, "DISCOVERED_FROM")

    # Vulnerabilities
    vulns = list(
        Vulnerability.objects.filter(target_id=target_id).select_related(
            "ip_asset", "subdomain_asset", "url_asset", "cve_intelligence"
        )[:max_vuln]
    )
    for v in vulns:
        nid = _node_id("vulnerability", v.id)
        cve = ""
        if v.cve_intelligence_id:
            cve = getattr(v.cve_intelligence, "cve_id", "") or ""
        label = v.name or cve or f"Vuln#{v.id}"
        add_node(
            nid,
            "vulnerability",
            label,
            v.id,
            {"severity": v.severity if hasattr(v, "severity") else None, "cve": cve},
        )
        attached = False
        if v.url_asset_id:
            un = _node_id("url", v.url_asset_id)
            if un in nodes:
                add_edge(un, nid, "DISCOVERED_FROM")
                attached = True
        if v.subdomain_asset_id:
            sn = _node_id("subdomain", v.subdomain_asset_id)
            if sn in nodes:
                add_edge(sn, nid, "DISCOVERED_FROM")
                attached = True
        if v.ip_asset_id:
            inn = _node_id("ip", v.ip_asset_id)
            if inn in nodes:
                add_edge(inn, nid, "DISCOVERED_FROM")
                attached = True
        if not attached:
            add_edge(target_nid, nid, "DISCOVERED_FROM")

    # AssetEdge explicit edges
    def edge_endpoint(kind: str, edge_obj, prefix: str) -> Optional[str]:
        # prefix is from_ or to_
        type_field = f"{prefix}asset_type"
        asset_type = (getattr(edge_obj, type_field, "") or "").upper()
        fk_map = {
            "IP": f"{prefix}ip",
            "SUBDOMAIN": f"{prefix}subdomain",
            "URL": f"{prefix}url",
            "ENDPOINT": f"{prefix}endpoint",
            "PORT": f"{prefix}port",
        }
        fk = fk_map.get(asset_type)
        if not fk:
            return None
        obj = getattr(edge_obj, fk, None)
        if obj is None:
            # try _id
            obj_id = getattr(edge_obj, f"{fk}_id", None)
            if not obj_id:
                return None
            type_key = asset_type.lower() if asset_type != "SUBDOMAIN" else "subdomain"
            if asset_type == "URL":
                type_key = "url"
            return _node_id(type_key, obj_id)
        type_key = {
            "IP": "ip",
            "SUBDOMAIN": "subdomain",
            "URL": "url",
            "ENDPOINT": "endpoint",
            "PORT": "port",
        }.get(asset_type, asset_type.lower())
        nid = _node_id(type_key, obj.id)
        if nid not in nodes:
            label = str(obj)
            add_node(nid, type_key, label, obj.id)
        return nid

    for ae in AssetEdge.objects.filter(target_id=target_id).select_related(
        "from_ip",
        "from_subdomain",
        "from_url",
        "from_endpoint",
        "from_port",
        "to_ip",
        "to_subdomain",
        "to_url",
        "to_endpoint",
        "to_port",
    )[:200]:
        src = edge_endpoint(ae.from_asset_type, ae, "from_")
        dst = edge_endpoint(ae.to_asset_type, ae, "to_")
        if src and dst:
            add_edge(src, dst, ae.edge_type or "CUSTOM", source_kind="asset_edge")

    active = get_active_attacks(target_id)
    active_ids = {a["node_id"] for a in active if a.get("node_id")}
    for nid in active_ids:
        if nid in nodes:
            nodes[nid]["is_active_attack"] = True

    return {
        "target_id": target.id,
        "target_name": target.name,
        "nodes": list(nodes.values()),
        "edges": edges,
        "active_attacks": active,
    }


def get_asset_pentest_records(asset_type: str, asset_id: int) -> dict:
    """Actions linked via Action.asset_links / AttackVector + related vulns/CVEs."""
    from apps.core.models import Action, AssetVectorLink, Vulnerability

    asset_type = (asset_type or "").lower()
    type_map = {
        "ip": "ip_asset_id",
        "subdomain": "subdomain_asset_id",
        "url": "url_asset_id",
        "endpoint": "endpoint_asset_id",
        "port": "port_asset_id",
    }
    if asset_type not in type_map:
        return None

    fk_id = type_map[asset_type]
    action_map: dict[int, Any] = {}

    # Actions that directly link this asset via M2M AssetVectorLink
    for a in (
        Action.objects.filter(**{f"asset_links__{fk_id}": asset_id})
        .distinct()
        .prefetch_related("action_vectors")
        .order_by("-created_at")[:50]
    ):
        action_map[a.id] = a

    # Actions that share an attack vector targeting this asset
    vector_ids = list(
        AssetVectorLink.objects.filter(**{fk_id: asset_id}).values_list(
            "attack_vector_id", flat=True
        )[:50]
    )
    if vector_ids:
        for a in (
            Action.objects.filter(action_vectors__attack_vector_id__in=vector_ids)
            .distinct()
            .prefetch_related("action_vectors")
            .order_by("-created_at")[:50]
        ):
            action_map.setdefault(a.id, a)

    records = []
    for a in action_map.values():
        purpose_val = a.purpose_text or ""
        if not purpose_val and a.purpose:
            purpose_val = a.purpose if isinstance(a.purpose, str) else str(a.purpose)
        records.append(
            {
                "action_id": a.id,
                "purpose": purpose_val[:500],
                "purpose_text": a.purpose_text or "",
                "status": a.status or "",
                "result_summary": a.result_summary or "",
                "plan_id": a.plan_id,
                "execution_graph_id": a.execution_graph_id,
                "started_at": a.started_at,
                "completed_at": a.completed_at,
                "attack_vector_ids": list(
                    a.action_vectors.values_list("attack_vector_id", flat=True)[:20]
                ),
            }
        )

    vuln_qs = Vulnerability.objects.filter(**{fk_id: asset_id}).select_related(
        "cve_intelligence"
    )[:30]
    vulns = []
    cves = []
    seen_cve: set[int] = set()
    for v in vuln_qs:
        vulns.append(
            {
                "id": v.id,
                "name": v.name,
                "severity": getattr(v, "severity", None),
                "status": getattr(v, "status", None),
            }
        )
        if v.cve_intelligence_id and v.cve_intelligence_id not in seen_cve:
            seen_cve.add(v.cve_intelligence_id)
            cve = v.cve_intelligence
            cves.append(
                {
                    "id": cve.id,
                    "cve_id": getattr(cve, "cve_id", None),
                    "cvss_score": getattr(cve, "cvss_score", None),
                    "title": getattr(cve, "title", None) or getattr(cve, "summary", None),
                }
            )

    return {
        "asset_type": asset_type,
        "asset_id": asset_id,
        "label": f"{asset_type}#{asset_id}",
        "records": records,
        "cves": cves,
        "vulnerabilities": vulns,
    }


def build_dispatch_tree(root_thread_id: int, max_depth: int = 4) -> dict:
    """Build nested SubAgentDispatch tree from a root (usually HackerAssistant) thread."""
    from apps.core.models import ExecutionGraph, SubAgentDispatch, Thread

    root = Thread.objects.filter(id=root_thread_id).first()
    if not root:
        return None

    def children_of(dispatcher_thread_id: int, depth: int, round_base: int) -> list[dict]:
        if depth > max_depth:
            return []
        rows = (
            SubAgentDispatch.objects.filter(dispatcher_thread_id=dispatcher_thread_id)
            .order_by("dispatched_at")
        )
        result = []
        for i, d in enumerate(rows, start=1):
            graph = None
            if d.sub_thread_id:
                graph = (
                    ExecutionGraph.objects.filter(thread_id=d.sub_thread_id)
                    .order_by("-started_at")
                    .first()
                )
            node = {
                "thread_id": d.sub_thread_id or 0,
                "dispatch_id": d.id,
                "agent_id": d.sub_agent_type or "",
                "status": d.status,
                "depth": depth,
                "round": round_base + i - 1 if depth == 1 else i,
                "objective": (d.objective or "")[:300],
                "dispatched_at": d.dispatched_at,
                "completed_at": d.completed_at,
                "graph_id": graph.id if graph else None,
                "children": [],
            }
            if d.sub_thread_id:
                node["children"] = children_of(d.sub_thread_id, depth + 1, 1)
            result.append(node)
        return result

    return {
        "root_thread_id": root.id,
        "root_agent_id": root.assistant_id or "",
        "nodes": children_of(root.id, depth=1, round_base=1),
    }

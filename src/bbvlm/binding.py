"""Strict transport binding for visual-model structure proposals.

The model sees short, randomly assigned visual tokens.  This module validates
the response against the trusted request and only then maps tokens back to the
stable graph/XML identifiers.  Token repair is deliberately forbidden.
"""
from __future__ import annotations


VALID_ROLES = {"MASTHEAD", "HEADER", "TEXT", "ADVERT", "OTHER", "UNKNOWN"}
VALID_GROUP_KINDS = {"ARTICLE", "NOTICE", "ADVERT", "MASTHEAD", "OTHER", "UNKNOWN"}
VALID_PHYSICAL_ROLES = {"MASTHEAD", "HEADER", "TEXT", "OTHER", "UNKNOWN"}
VALID_COARSE_ROLES = {"STREAM", "MASTHEAD", "OTHER", "UNKNOWN"}
VALID_EDITORIAL_GENRES = {"ARTICLE", "ADVERT", "NOTICE", "MASTHEAD", "OTHER", "UNKNOWN"}


def _exact_partition(values, expected, field):
    flat = list(values)
    if len(flat) != len(set(flat)) or set(flat) != set(expected):
        raise ValueError(f"{field} must contain every allowed token exactly once")


def bind_olr_page(response, token_to_id):
    """Validate one page response and bind all tokens to stable identifiers."""
    expected = set(token_to_id)
    ordered = response.get("ordered_tokens")
    groups = response.get("groups")
    roles = response.get("roles")
    if not isinstance(ordered, list) or not isinstance(groups, list) or not isinstance(roles, dict):
        raise ValueError("ordered_tokens, groups and roles are required")
    _exact_partition(ordered, expected, "ordered_tokens")
    grouped = []
    for group in groups:
        tokens = group.get("tokens") if isinstance(group, dict) else None
        if not isinstance(tokens, list) or not tokens:
            raise ValueError("each group requires a non-empty tokens list")
        grouped.extend(tokens)
    _exact_partition(grouped, expected, "groups")
    group_ids = [group.get("id") for group in groups]
    if any(not isinstance(gid, str) or not gid for gid in group_ids) or len(group_ids) != len(set(group_ids)):
        raise ValueError("group IDs must be non-empty and unique within the page")
    if set(roles) != expected or any(v not in VALID_ROLES for v in roles.values()):
        raise ValueError("roles must cover every allowed token with a controlled value")
    uncertain = response.get("uncertain_tokens", [])
    if not isinstance(uncertain, list) or len(uncertain) != len(set(uncertain)) or not set(uncertain) <= expected:
        raise ValueError("uncertain_tokens must be a unique subset of allowed tokens")
    return {
        "page": response.get("page"),
        "ordered_region_ids": [token_to_id[t] for t in ordered],
        "groups": [
            {
                "id": group.get("id"),
                "region_ids": [token_to_id[t] for t in group["tokens"]],
                "label": group.get("label", ""),
                "uncertain": bool(group.get("uncertain", False)),
            }
            for group in groups
        ],
        "roles": {token_to_id[t]: role for t, role in roles.items()},
        "uncertain_region_ids": [token_to_id[t] for t in uncertain],
        "notes": response.get("notes", ""),
    }


def bind_semantic_page(response, token_to_id):
    """Strictly bind a role/eligibility/grouping response without an order field.

    Reading order is intentionally absent: the semantic reader must not spend a
    model pass reproducing an order that the frozen geometry path already emits.
    """
    expected = set(token_to_id)
    groups = response.get("groups")
    roles = response.get("roles")
    eligible = response.get("eligible_tokens")
    if not isinstance(groups, list) or not isinstance(roles, dict) or not isinstance(eligible, list):
        raise ValueError("groups, roles and eligible_tokens are required")
    grouped = []
    for group in groups:
        tokens = group.get("tokens") if isinstance(group, dict) else None
        if not isinstance(tokens, list) or not tokens:
            raise ValueError("each group requires a non-empty tokens list")
        grouped.extend(tokens)
        if group.get("kind") not in VALID_GROUP_KINDS:
            raise ValueError("group kind must be controlled")
    _exact_partition(grouped, expected, "groups")
    group_ids = [group.get("id") for group in groups]
    if any(not isinstance(gid, str) or not gid for gid in group_ids) or len(group_ids) != len(set(group_ids)):
        raise ValueError("group IDs must be non-empty and unique within the page")
    if set(roles) != expected or any(v not in VALID_ROLES for v in roles.values()):
        raise ValueError("roles must cover every allowed token with a controlled value")
    if len(eligible) != len(set(eligible)) or not set(eligible) <= expected:
        raise ValueError("eligible_tokens must be a unique subset of allowed tokens")
    uncertain = response.get("uncertain_tokens", [])
    if not isinstance(uncertain, list) or len(uncertain) != len(set(uncertain)) or not set(uncertain) <= expected:
        raise ValueError("uncertain_tokens must be a unique subset of allowed tokens")
    return {
        "page": response.get("page"),
        "eligible_region_ids": [token_to_id[t] for t in eligible],
        "groups": [
            {
                "id": group["id"],
                "region_ids": [token_to_id[t] for t in group["tokens"]],
                "kind": group["kind"],
                "label": group.get("label", ""),
                "uncertain": bool(group.get("uncertain", False)),
            }
            for group in groups
        ],
        "roles": {token_to_id[t]: role for t, role in roles.items()},
        "uncertain_region_ids": [token_to_id[t] for t in uncertain],
        "notes": response.get("notes", ""),
    }


def bind_role_filter_page(response, token_to_id):
    """Bind the minimal VLM output used by deterministic SSU/order logic."""
    expected = set(token_to_id)
    roles = response.get("roles")
    eligible = response.get("eligible_tokens")
    if not isinstance(roles, dict) or not isinstance(eligible, list):
        raise ValueError("roles and eligible_tokens are required")
    if set(roles) != expected or any(v not in VALID_ROLES for v in roles.values()):
        raise ValueError("roles must cover every allowed token with a controlled value")
    if len(eligible) != len(set(eligible)) or not set(eligible) <= expected:
        raise ValueError("eligible_tokens must be a unique subset of allowed tokens")
    uncertain = response.get("uncertain_tokens", [])
    if not isinstance(uncertain, list) or len(uncertain) != len(set(uncertain)) or not set(uncertain) <= expected:
        raise ValueError("uncertain_tokens must be a unique subset of allowed tokens")
    return {
        "page": response.get("page"),
        "eligible_region_ids": [token_to_id[t] for t in eligible],
        "roles": {token_to_id[t]: role for t, role in roles.items()},
        "uncertain_region_ids": [token_to_id[t] for t in uncertain],
        "notes": response.get("notes", ""),
    }


def bind_faceted_page(response, token_to_id):
    """Bind separate physical-role and editorial-genre judgements.

    Stream membership is deliberately not accepted from the model.  It is
    derived later from the frozen physical profile so an editorial label such
    as ADVERT cannot silently delete readable content.
    """
    expected = set(token_to_id)
    physical = response.get("physical_roles")
    genres = response.get("editorial_genres")
    if not isinstance(physical, dict) or not isinstance(genres, dict):
        raise ValueError("physical_roles and editorial_genres are required")
    if set(physical) != expected or any(v not in VALID_PHYSICAL_ROLES for v in physical.values()):
        raise ValueError("physical_roles must cover every allowed token with a controlled value")
    if set(genres) != expected or any(v not in VALID_EDITORIAL_GENRES for v in genres.values()):
        raise ValueError("editorial_genres must cover every allowed token with a controlled value")
    result = {
        "page": response.get("page"),
        "physical_roles": {token_to_id[t]: role for t, role in physical.items()},
        "editorial_genres": {token_to_id[t]: genre for t, genre in genres.items()},
        "notes": response.get("notes", ""),
    }
    for source, target in (("uncertain_physical_tokens", "uncertain_physical_region_ids"),
                           ("uncertain_genre_tokens", "uncertain_genre_region_ids")):
        values = response.get(source, [])
        if not isinstance(values, list) or len(values) != len(set(values)) or not set(values) <= expected:
            raise ValueError(f"{source} must be a unique subset of allowed tokens")
        result[target] = [token_to_id[t] for t in values]
    return result


def bind_coarse_faceted_page(response, token_to_id):
    """Bind coarse physical stream membership and independent genre labels.

    HEADER versus TEXT is intentionally absent from the model contract.  The
    caller must refine STREAM using a frozen deterministic rule.  As with the
    fine faceted binder, genre can never control physical stream membership.
    """
    expected = set(token_to_id)
    coarse = response.get("coarse_roles")
    genres = response.get("editorial_genres")
    if not isinstance(coarse, dict) or not isinstance(genres, dict):
        raise ValueError("coarse_roles and editorial_genres are required")
    if set(coarse) != expected or any(v not in VALID_COARSE_ROLES for v in coarse.values()):
        raise ValueError("coarse_roles must cover every allowed token with a controlled value")
    if set(genres) != expected or any(v not in VALID_EDITORIAL_GENRES for v in genres.values()):
        raise ValueError("editorial_genres must cover every allowed token with a controlled value")
    result = {
        "page": response.get("page"),
        "coarse_roles": {token_to_id[t]: role for t, role in coarse.items()},
        "editorial_genres": {token_to_id[t]: genre for t, genre in genres.items()},
        "notes": response.get("notes", ""),
    }
    for source, target in (("uncertain_coarse_tokens", "uncertain_coarse_region_ids"),
                           ("uncertain_genre_tokens", "uncertain_genre_region_ids")):
        values = response.get(source, [])
        if not isinstance(values, list) or len(values) != len(set(values)) or not set(values) <= expected:
            raise ValueError(f"{source} must be a unique subset of allowed tokens")
        result[target] = [token_to_id[t] for t in values]
    return result

#!/usr/bin/env python3
"""Validate one token source and build the five visual-token artifacts."""

from __future__ import annotations

import argparse
import copy
import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


EXTENSION_KEY = "com.website-uiux-extractor"
REQUIRED_GROUPS = ("color", "typography", "spacing", "radius")
OPTIONAL_GROUPS = ("shadow", "duration", "easing", "breakpoint")
TOKEN_GROUPS = REQUIRED_GROUPS + OPTIONAL_GROUPS
GROUP_TYPES = {
    "color": "color",
    "typography": "typography",
    "spacing": "dimension",
    "radius": "dimension",
    "shadow": "shadow",
    "duration": "duration",
    "easing": "cubicBezier",
    "breakpoint": "dimension",
}
GROUP_PREFIXES = {
    "color": "color",
    "spacing": "spacing",
    "radius": "radius",
    "shadow": "shadow",
    "duration": "duration",
    "easing": "ease",
    "breakpoint": "breakpoint",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALIAS_RE = re.compile(r"^\{([a-z0-9-]+)\.([a-z0-9-]+)\}$")
REFERENCE_RE = re.compile(r"\{([a-z0-9-]+)\.([a-z0-9-]+)\}")
UNSAFE_CSS_RE = re.compile(r"[;{}<>\r\n]")
SPECIMEN_KINDS = {
    "button",
    "icon-button",
    "input",
    "textarea",
    "switch",
    "slider",
    "tabs",
    "card",
    "panel",
    "composer",
}
SPECIMEN_STYLE_PROPERTIES = {
    "backgroundColor": "background-color",
    "textColor": "color",
    "borderColor": "border-color",
    "border": "border",
    "radius": "border-radius",
    "borderRadius": "border-radius",
    "cardRadius": "border-radius",
    "shadow": "box-shadow",
    "cardShadow": "box-shadow",
    "width": "width",
    "height": "height",
    "minHeight": "min-height",
    "padding": "padding",
    "gap": "gap",
    "opacity": "opacity",
    "outlineColor": "outline-color",
    "trackColor": "--spec-track",
    "fillColor": "--spec-fill",
    "thumbColor": "--spec-thumb",
    "selectedTextColor": "--spec-selected-color",
    "inactiveTextColor": "--spec-inactive-color",
}


class ContractError(ValueError):
    pass


def _json_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _dedupe_list(values: Any) -> tuple[Any, int]:
    if not isinstance(values, list):
        return values, 0
    seen: set[str] = set()
    result = []
    removed = 0
    for value in values:
        key = _json_key(value)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        result.append(value)
    return result, removed


def normalize(data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Remove exact list duplicates and merge duplicate route observations."""
    result = copy.deepcopy(data)
    removed = 0
    ext = result.get("$extensions", {}).get(EXTENSION_KEY, {})
    if not isinstance(ext, dict):
        return result, removed

    coverage = ext.get("coverage", {})
    if isinstance(coverage, dict):
        for key in ("viewports", "gaps"):
            coverage[key], count = _dedupe_list(coverage.get(key, []))
            removed += count

        routes = coverage.get("routes")
        if isinstance(routes, list):
            merged: dict[tuple[Any, Any], dict[str, Any]] = {}
            order: list[tuple[Any, Any]] = []
            passthrough: list[Any] = []
            for route in routes:
                if not isinstance(route, dict):
                    passthrough.append(route)
                    continue
                route = copy.deepcopy(route)
                route["states"], count = _dedupe_list(route.get("states"))
                removed += count
                key = (route.get("url"), route.get("family"))
                if key not in merged:
                    merged[key] = route
                    order.append(key)
                    continue
                existing = merged[key]
                left = {k: v for k, v in existing.items() if k != "states"}
                right = {k: v for k, v in route.items() if k != "states"}
                if left != right:
                    raise ContractError(
                        f"Conflicting duplicate route for {key[0]!r} / {key[1]!r}."
                    )
                combined = list(existing.get("states") or []) + list(route.get("states") or [])
                existing["states"], count = _dedupe_list(combined)
                removed += 1 + count
            coverage["routes"] = [merged[key] for key in order] + passthrough

    components = ext.get("components")
    if isinstance(components, list):
        unique_components: list[Any] = []
        by_name: dict[Any, dict[str, Any]] = {}
        for component in components:
            if not isinstance(component, dict):
                unique_components.append(component)
                continue
            component = copy.deepcopy(component)
            for key in ("states", "evidence"):
                component[key], count = _dedupe_list(component.get(key))
                removed += count
            name = component.get("name")
            if name not in by_name:
                by_name[name] = component
                unique_components.append(component)
            elif by_name[name] == component:
                removed += 1
            else:
                raise ContractError(f"Conflicting duplicate component named {name!r}.")
        ext["components"] = unique_components

    guidelines = ext.get("guidelines")
    if isinstance(guidelines, dict):
        for key in ("do", "avoid"):
            guidelines[key], count = _dedupe_list(guidelines.get(key, []))
            removed += count
    for key in ("responsiveNotes", "motionNotes"):
        ext[key], count = _dedupe_list(ext.get(key, []))
        removed += count
    return result, removed


def _alias_target(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None
    match = ALIAS_RE.fullmatch(value)
    return (match.group(1), match.group(2)) if match else None


def _token(data: dict[str, Any], group: str, name: str) -> dict[str, Any]:
    tokens = data.get(group)
    if not isinstance(tokens, dict) or name not in tokens or not isinstance(tokens[name], dict):
        raise ContractError(f"Unknown token reference {{{group}.{name}}}.")
    return tokens[name]


def resolve_value(
    data: dict[str, Any], group: str, name: str, trail: tuple[tuple[str, str], ...] = ()
) -> Any:
    current = (group, name)
    if current in trail:
        chain = " -> ".join(f"{{{g}.{n}}}" for g, n in trail + (current,))
        raise ContractError(f"Circular token alias: {chain}.")
    value = _token(data, group, name).get("$value")
    target = _alias_target(value)
    if target is None:
        return value
    return resolve_value(data, target[0], target[1], trail + (current,))


def _valid_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_css_scalar(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, (int, float)):
        return
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty CSS scalar.")
        return
    if _alias_target(value):
        return
    if UNSAFE_CSS_RE.search(value):
        errors.append(f"{path} contains unsafe CSS delimiter characters.")


def _validate_specimen_style(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, (int, float)):
        return
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty CSS scalar.")
        return
    scrubbed = REFERENCE_RE.sub("", value)
    if UNSAFE_CSS_RE.search(scrubbed):
        errors.append(f"{path} contains unsafe CSS delimiter characters.")


def _validate_shadow(value: Any, path: str, errors: list[str]) -> None:
    shadows = value if isinstance(value, list) else [value]
    if not shadows:
        errors.append(f"{path} must contain at least one shadow.")
        return
    for index, shadow in enumerate(shadows):
        item_path = f"{path}[{index}]"
        if isinstance(shadow, str):
            _validate_css_scalar(shadow, item_path, errors)
            continue
        if not isinstance(shadow, dict):
            errors.append(f"{item_path} must be a CSS string or shadow object.")
            continue
        for key in ("color", "offsetX", "offsetY", "blur", "spread"):
            if key not in shadow:
                errors.append(f"{item_path}.{key} is required.")
            else:
                _validate_css_scalar(shadow[key], f"{item_path}.{key}", errors)
        if "inset" in shadow and not isinstance(shadow["inset"], bool):
            errors.append(f"{item_path}.inset must be boolean.")


def validate(data: dict[str, Any]) -> None:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise ContractError("Token source must be a JSON object.")

    if not isinstance(data.get("$schema"), str):
        errors.append("$schema is required.")
    if not isinstance(data.get("$description"), str) or not data["$description"].strip():
        errors.append("$description is required.")

    meta = data.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta must be an object.")
    else:
        for key in ("name", "description", "theme"):
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                errors.append(f"meta.{key} is required.")

    extensions = data.get("$extensions")
    ext = extensions.get(EXTENSION_KEY) if isinstance(extensions, dict) else None
    if not isinstance(ext, dict):
        errors.append(f"$extensions.{EXTENSION_KEY} must be an object.")
        ext = {}

    source = ext.get("source")
    if not isinstance(source, dict):
        errors.append(f"$extensions.{EXTENSION_KEY}.source must be an object.")
    else:
        if not _valid_http_url(source.get("url")):
            errors.append("source.url must be an HTTP(S) URL.")
        if not isinstance(source.get("capturedAt"), str) or not source["capturedAt"].strip():
            errors.append("source.capturedAt is required.")

    coverage = ext.get("coverage")
    if not isinstance(coverage, dict):
        errors.append(f"$extensions.{EXTENSION_KEY}.coverage must be an object.")
        coverage = {}
    viewports = coverage.get("viewports")
    if not isinstance(viewports, list) or len(viewports) < 2:
        errors.append("coverage.viewports must contain at least desktop and mobile viewports.")
        viewports = []
    elif not all(isinstance(viewport, str) and viewport.strip() for viewport in viewports):
        errors.append("coverage.viewports must contain non-empty strings.")
    routes = coverage.get("routes")
    if not isinstance(routes, list) or not routes:
        errors.append("coverage.routes must contain at least one representative route.")
    elif isinstance(routes, list):
        for index, route in enumerate(routes):
            if not isinstance(route, dict):
                errors.append(f"coverage.routes[{index}] must be an object.")
                continue
            if not _valid_http_url(route.get("url")):
                errors.append(f"coverage.routes[{index}].url must be HTTP(S).")
            if not isinstance(route.get("family"), str) or not route["family"].strip():
                errors.append(f"coverage.routes[{index}].family is required.")
            if not isinstance(route.get("states"), list) or not route["states"]:
                errors.append(f"coverage.routes[{index}].states must be non-empty.")

    for group in TOKEN_GROUPS:
        tokens = data.get(group)
        if group in REQUIRED_GROUPS and (not isinstance(tokens, dict) or not tokens):
            errors.append(f"{group} must be a non-empty object.")
            continue
        if tokens is None:
            continue
        if not isinstance(tokens, dict):
            errors.append(f"{group} must be an object.")
            continue

        literal_values: dict[str, str] = {}
        for name, token in tokens.items():
            path = f"{group}.{name}"
            if not NAME_RE.fullmatch(str(name)):
                errors.append(f"{path} must use lowercase kebab-case.")
            if not isinstance(token, dict):
                errors.append(f"{path} must be an object.")
                continue
            if "$value" not in token:
                errors.append(f"{path}.$value is required.")
                continue
            if token.get("$type") != GROUP_TYPES[group]:
                errors.append(f"{path}.$type must be {GROUP_TYPES[group]!r}.")
            if not isinstance(token.get("$description"), str) or not token["$description"].strip():
                errors.append(f"{path}.$description is required.")

            value = token["$value"]
            target = _alias_target(value)
            if target:
                if target[0] != group:
                    errors.append(f"{path} alias must stay within the {group} group.")
                try:
                    resolve_value(data, group, name)
                except ContractError as exc:
                    errors.append(str(exc))
                continue

            value_key = _json_key(value)
            if value_key in literal_values:
                errors.append(
                    f"{path} repeats the literal value of {group}.{literal_values[value_key]}; "
                    "keep one literal and make the other token an alias."
                )
            else:
                literal_values[value_key] = name

            if group == "typography":
                if not isinstance(value, dict):
                    errors.append(f"{path}.$value must be a typography object.")
                    continue
                for key in ("fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing"):
                    if key not in value:
                        errors.append(f"{path}.$value.{key} is required.")
                    else:
                        _validate_css_scalar(value[key], f"{path}.$value.{key}", errors)
            elif group == "shadow":
                _validate_shadow(value, f"{path}.$value", errors)
            elif group == "easing" and isinstance(value, list):
                if len(value) != 4 or not all(isinstance(number, (int, float)) for number in value):
                    errors.append(f"{path}.$value must contain four numbers.")
            else:
                _validate_css_scalar(value, f"{path}.$value", errors)

    components = ext.get("components")
    if not isinstance(components, list) or not components:
        errors.append(f"$extensions.{EXTENSION_KEY}.components must be non-empty.")
    elif isinstance(components, list):
        component_names: set[str] = set()
        for index, component in enumerate(components):
            path = f"components[{index}]"
            if not isinstance(component, dict):
                errors.append(f"{path} must be an object.")
                continue
            name = component.get("name")
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                errors.append(f"{path}.name must use lowercase kebab-case.")
            elif name in component_names:
                errors.append(f"{path}.name duplicates {name!r}.")
            else:
                component_names.add(name)
            for key in ("role", "properties"):
                expected = str if key == "role" else dict
                if not isinstance(component.get(key), expected) or not component[key]:
                    errors.append(f"{path}.{key} is required.")
            if not isinstance(component.get("states"), list) or not component["states"]:
                errors.append(f"{path}.states must be non-empty.")
            if not isinstance(component.get("evidence"), list) or not component["evidence"]:
                errors.append(f"{path}.evidence must be non-empty.")
            else:
                for evidence_index, evidence in enumerate(component["evidence"]):
                    evidence_path = f"{path}.evidence[{evidence_index}]"
                    if not isinstance(evidence, dict):
                        errors.append(f"{evidence_path} must be an object.")
                        continue
                    if not _valid_http_url(evidence.get("url")):
                        errors.append(f"{evidence_path}.url must be HTTP(S).")
                    if evidence.get("viewport") not in viewports:
                        errors.append(f"{evidence_path}.viewport must match coverage.viewports.")
                    if evidence.get("state") not in component.get("states", []):
                        errors.append(f"{evidence_path}.state must match the component states.")
            properties = component.get("properties")
            if isinstance(properties, dict):
                for prop_name, prop_value in properties.items():
                    if not isinstance(prop_name, str) or not prop_name:
                        errors.append(f"{path}.properties contains an invalid name.")
                    if isinstance(prop_value, str):
                        for match in REFERENCE_RE.finditer(prop_value):
                            try:
                                _token(data, match.group(1), match.group(2))
                            except ContractError as exc:
                                errors.append(f"{path}.properties.{prop_name}: {exc}")
                    if prop_name in SPECIMEN_STYLE_PROPERTIES or prop_name in {"size", "typography"}:
                        _validate_specimen_style(
                            prop_value, f"{path}.properties.{prop_name}", errors
                        )

            specimen = component.get("specimen")
            if not isinstance(specimen, dict):
                errors.append(f"{path}.specimen is required for the visual preview.")
                continue
            kind = specimen.get("kind")
            if kind not in SPECIMEN_KINDS:
                errors.append(
                    f"{path}.specimen.kind must be one of {', '.join(sorted(SPECIMEN_KINDS))}."
                )
            if not isinstance(specimen.get("label"), str) or not specimen["label"].strip():
                errors.append(f"{path}.specimen.label is required.")
            if kind == "tabs" and (
                not isinstance(specimen.get("secondaryLabel"), str)
                or not specimen["secondaryLabel"].strip()
            ):
                errors.append(f"{path}.specimen.secondaryLabel is required for tabs.")
            if kind == "slider":
                slider_values = [specimen.get(key) for key in ("min", "max", "step", "value")]
                if not all(isinstance(value, (int, float)) for value in slider_values):
                    errors.append(f"{path}.specimen slider min, max, step, and value must be numbers.")
                elif specimen["min"] >= specimen["max"] or specimen["step"] <= 0:
                    errors.append(f"{path}.specimen slider range and step are invalid.")
                elif not specimen["min"] <= specimen["value"] <= specimen["max"]:
                    errors.append(f"{path}.specimen.value must fall inside the slider range.")

            specimen_states = specimen.get("states")
            if not isinstance(specimen_states, dict) or not specimen_states:
                errors.append(f"{path}.specimen.states must be a non-empty object.")
                continue
            for state_name, state_config in specimen_states.items():
                state_path = f"{path}.specimen.states.{state_name}"
                if state_name not in component.get("states", []):
                    errors.append(f"{state_path} must match the component states.")
                if not isinstance(state_config, dict):
                    errors.append(f"{state_path} must be an object.")
                    continue
                for flag in ("disabled", "checked", "toolsActive"):
                    if flag in state_config and not isinstance(state_config[flag], bool):
                        errors.append(f"{state_path}.{flag} must be boolean.")
                if "selectedIndex" in state_config and state_config["selectedIndex"] not in (0, 1):
                    errors.append(f"{state_path}.selectedIndex must be 0 or 1.")
                state_style = state_config.get("style", {})
                if not isinstance(state_style, dict):
                    errors.append(f"{state_path}.style must be an object.")
                    continue
                for prop_name, prop_value in state_style.items():
                    if prop_name not in SPECIMEN_STYLE_PROPERTIES and prop_name not in {
                        "size",
                        "typography",
                    }:
                        errors.append(f"{state_path}.style.{prop_name} is not previewable.")
                        continue
                    _validate_specimen_style(
                        prop_value, f"{state_path}.style.{prop_name}", errors
                    )
                    if isinstance(prop_value, str):
                        for match in REFERENCE_RE.finditer(prop_value):
                            try:
                                _token(data, match.group(1), match.group(2))
                            except ContractError as exc:
                                errors.append(f"{state_path}.style.{prop_name}: {exc}")

    if errors:
        raise ContractError("\n".join(f"- {error}" for error in errors))


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ContractError("Could not derive an ASCII slug; pass --slug explicitly.")
    return slug


def _css_var_name(group: str, name: str) -> str:
    if group not in GROUP_PREFIXES:
        raise ContractError(f"No CSS variable mapping for {group}.{name}.")
    return f"--{GROUP_PREFIXES[group]}-{name}"


def _shadow_to_css(value: Any) -> str:
    shadows = value if isinstance(value, list) else [value]
    parts = []
    for shadow in shadows:
        if isinstance(shadow, str):
            parts.append(shadow)
            continue
        prefix = "inset " if shadow.get("inset") else ""
        parts.append(
            f"{prefix}{shadow['offsetX']} {shadow['offsetY']} {shadow['blur']} "
            f"{shadow['spread']} {shadow['color']}"
        )
    return ", ".join(parts)


def _raw_css_value(group: str, value: Any) -> str:
    if group == "shadow":
        return _shadow_to_css(value)
    if group == "easing" and isinstance(value, list):
        return "cubic-bezier(" + ", ".join(str(number) for number in value) + ")"
    return str(value)


def css_declarations(data: dict[str, Any]) -> list[str]:
    declarations: list[str] = []
    families: list[str] = []
    for name in data["typography"]:
        value = resolve_value(data, "typography", name)
        family = value["fontFamily"]
        if family not in families:
            families.append(family)
    for index, family in enumerate(families):
        variable = "--font-primary" if index == 0 else f"--font-family-{index + 1}"
        declarations.append(f"{variable}: {family};")

    for group in TOKEN_GROUPS:
        tokens = data.get(group, {})
        for name, token in tokens.items():
            value = token["$value"]
            target = _alias_target(value)
            if group == "typography":
                if target:
                    target_name = target[1]
                    declarations.extend(
                        [
                            f"--text-{name}: var(--text-{target_name});",
                            f"--font-weight-{name}: var(--font-weight-{target_name});",
                            f"--leading-{name}: var(--leading-{target_name});",
                            f"--tracking-{name}: var(--tracking-{target_name});",
                        ]
                    )
                else:
                    declarations.extend(
                        [
                            f"--text-{name}: {value['fontSize']};",
                            f"--font-weight-{name}: {value['fontWeight']};",
                            f"--leading-{name}: {value['lineHeight']};",
                            f"--tracking-{name}: {value['letterSpacing']};",
                        ]
                    )
                continue
            variable = _css_var_name(group, name)
            css_value = f"var({_css_var_name(*target)})" if target else _raw_css_value(group, value)
            declarations.append(f"{variable}: {css_value};")
    return declarations


def render_css(data: dict[str, Any], selector: str, label: str) -> str:
    name = data["meta"]["name"]
    declarations = "\n".join(f"  {line}" for line in css_declarations(data))
    return f"/* {name} {label} */\n{selector} {{\n{declarations}\n}}\n"


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _display_value(data: dict[str, Any], group: str, name: str) -> str:
    value = resolve_value(data, group, name)
    if group == "typography":
        return (
            f"{value['fontSize']} / {value['fontWeight']} / {value['lineHeight']} / "
            f"{value['letterSpacing']}"
        )
    return _raw_css_value(group, value)


def render_design_md(data: dict[str, Any]) -> str:
    meta = data["meta"]
    ext = data["$extensions"][EXTENSION_KEY]
    source = ext["source"]
    coverage = ext["coverage"]
    lines = [
        f"# {meta['name']} — Style Reference",
        f"> {meta['description']}",
        "",
        f"**Theme:** {meta['theme']}",
        "",
        f"**Source website:** [{source['url']}]({source['url']})  ",
        f"**Captured:** {source['capturedAt']}  ",
        "Use the live source website to compare and validate this extracted snapshot. The current source remains authoritative.",
        "",
        "## Tokens — Colors",
        "",
        "| Name | Value | Token | Role |",
        "|---|---|---|---|",
    ]
    for name, token in data["color"].items():
        alias = _alias_target(token["$value"])
        role = token["$description"]
        if alias:
            role += f" Alias of `{{{alias[0]}.{alias[1]}}}`."
        lines.append(
            f"| {_md(name)} | `{_md(_display_value(data, 'color', name))}` | "
            f"`--color-{name}` | {_md(role)} |"
        )

    lines.extend(
        [
            "",
            "## Tokens — Typography",
            "",
            "| Role | Family | Size | Weight | Line Height | Letter Spacing | Token |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for name in data["typography"]:
        value = resolve_value(data, "typography", name)
        lines.append(
            f"| {_md(name)} | {_md(value['fontFamily'])} | `{value['fontSize']}` | "
            f"{value['fontWeight']} | {value['lineHeight']} | `{value['letterSpacing']}` | `--text-{name}` |"
        )

    lines.extend(["", "## Tokens — Spacing & Shapes", ""])
    for group, heading, variable_prefix in (
        ("spacing", "Spacing Scale", "spacing"),
        ("radius", "Border Radius", "radius"),
    ):
        lines.extend(
            [
                f"### {heading}",
                "",
                "| Name | Value | Token | Role |",
                "|---|---|---|---|",
            ]
        )
        for name, token in data[group].items():
            lines.append(
                f"| {_md(name)} | `{_md(_display_value(data, group, name))}` | "
                f"`--{variable_prefix}-{name}` | {_md(token['$description'])} |"
            )
        lines.append("")

    if data.get("shadow"):
        lines.extend(
            [
                "## Tokens — Depth",
                "",
                "| Name | Value | Token | Role |",
                "|---|---|---|---|",
            ]
        )
        for name, token in data["shadow"].items():
            lines.append(
                f"| {_md(name)} | `{_md(_display_value(data, 'shadow', name))}` | "
                f"`--shadow-{name}` | {_md(token['$description'])} |"
            )
        lines.append("")

    if data.get("duration") or data.get("easing"):
        lines.extend(
            [
                "## Tokens — Motion",
                "",
                "| Type | Name | Value | Role |",
                "|---|---|---|---|",
            ]
        )
        for group in ("duration", "easing"):
            for name, token in data.get(group, {}).items():
                lines.append(
                    f"| {group} | {_md(name)} | `{_md(_display_value(data, group, name))}` | "
                    f"{_md(token['$description'])} |"
                )
        lines.append("")

    lines.extend(["## Layout & Responsive", ""])
    for key, value in ext.get("layout", {}).items():
        lines.append(f"- **{_md(key)}:** `{_md(value)}`")
    for note in ext.get("responsiveNotes", []):
        lines.append(f"- {_md(note)}")
    for note in ext.get("motionNotes", []):
        lines.append(f"- **Motion:** {_md(note)}")

    lines.extend(["", "## Components", ""])
    for component in ext["components"]:
        preview_states = ", ".join(component["specimen"]["states"])
        lines.extend(
            [
                f"### {component['name']}",
                f"**Role:** {component['role']}",
                f"**Preview specimen:** `{component['specimen']['kind']}` · {preview_states}",
                "",
            ]
        )
        for key, value in component["properties"].items():
            lines.append(f"- **{_md(key)}:** `{_md(value)}`")
        lines.append(f"- **States checked:** {', '.join(_md(x) for x in component['states'])}")
        lines.append("- **Evidence:**")
        for evidence in component["evidence"]:
            summary = " · ".join(
                _md(evidence.get(key, "")) for key in ("viewport", "state", "note") if evidence.get(key)
            )
            lines.append(f"  - [{evidence.get('url', '')}]({evidence.get('url', '')}) — {summary}")
        lines.append("")

    guidelines = ext.get("guidelines", {})
    lines.extend(["## Do's and Don'ts", "", "### Do", ""])
    lines.extend(f"- {_md(item)}" for item in guidelines.get("do", []))
    lines.extend(["", "### Avoid", ""])
    lines.extend(f"- {_md(item)}" for item in guidelines.get("avoid", []))

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"**Viewports:** {', '.join(f'`{_md(x)}`' for x in coverage['viewports'])}",
            "",
            "| Page family | URL | States checked |",
            "|---|---|---|",
        ]
    )
    for route in coverage["routes"]:
        lines.append(
            f"| {_md(route['family'])} | [{_md(route['url'])}]({route['url']}) | "
            f"{', '.join(_md(x) for x in route['states'])} |"
        )
    lines.extend(["", "### Coverage gaps", ""])
    gaps = coverage.get("gaps", [])
    lines.extend(f"- {_md(gap)}" for gap in gaps) if gaps else lines.append("- None recorded.")
    return "\n".join(lines).rstrip() + "\n"


def _pick_var(data: dict[str, Any], group: str, names: tuple[str, ...], fallback: str) -> str:
    tokens = data.get(group, {})
    for name in names:
        if name in tokens:
            return f"var({_css_var_name(group, name)})"
    if tokens:
        first = next(iter(tokens))
        return f"var({_css_var_name(group, first)})"
    return fallback


def _visual_height(value: Any) -> int:
    text = str(value)
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 20
    number = abs(float(match.group()))
    if "rem" in text:
        number *= 16
    return round(min(100, max(8, number)))


def _preview_css_value(value: Any) -> str:
    if isinstance(value, (int, float)):
        return str(value)

    def replace_reference(match: re.Match[str]) -> str:
        group, name = match.group(1), match.group(2)
        if group == "typography":
            return f"var(--text-{name})"
        return f"var({_css_var_name(group, name)})"

    return REFERENCE_RE.sub(replace_reference, str(value))


def _specimen_inline_style(data: dict[str, Any], properties: dict[str, Any]) -> str:
    declarations: list[str] = []
    typography = properties.get("typography")
    target = _alias_target(typography)
    if target and target[0] == "typography":
        value = resolve_value(data, target[0], target[1])
        declarations.extend(
            [
                f"font-family:{value['fontFamily']}",
                f"font-size:{value['fontSize']}",
                f"font-weight:{value['fontWeight']}",
                f"line-height:{value['lineHeight']}",
                f"letter-spacing:{value['letterSpacing']}",
            ]
        )
    for key, css_property in SPECIMEN_STYLE_PROPERTIES.items():
        if key in properties:
            declarations.append(f"{css_property}:{_preview_css_value(properties[key])}")
    if "size" in properties:
        value = _preview_css_value(properties["size"])
        declarations.extend((f"width:{value}", f"height:{value}"))
    return ";".join(declarations)


def _render_specimen_element(
    data: dict[str, Any], component: dict[str, Any], state: str, config: dict[str, Any]
) -> str:
    specimen = component["specimen"]
    kind = specimen["kind"]
    esc = lambda value: html.escape(str(value), quote=True)
    properties = dict(component["properties"])
    properties.update(config.get("style", {}))
    style = _specimen_inline_style(data, properties)
    if kind == "slider":
        slider_value = config.get("value", specimen["value"])
        slider_span = specimen["max"] - specimen["min"]
        slider_position = (slider_value - specimen["min"]) / slider_span * 100
        style = f"{style};--spec-position:{slider_position:.2f}%".strip(";")
    style_attr = f' style="{esc(style)}"' if style else ""
    disabled = " disabled" if config.get("disabled") else ""
    label = esc(specimen["label"])
    value = config.get("value", specimen.get("value", ""))
    placeholder = esc(specimen.get("placeholder", specimen["label"]))

    if kind == "button":
        return f'<button type="button" class="specimen-control specimen-button"{style_attr}{disabled}>{label}</button>'
    if kind == "icon-button":
        glyph = esc(specimen.get("glyph", "+"))
        return f'<button type="button" class="specimen-control specimen-icon-button" aria-label="{label}"{style_attr}{disabled}>{glyph}</button>'
    if kind == "input":
        return (
            f'<label class="specimen-field"{style_attr}><span>{label}</span>'
            f'<input type="text" value="{esc(value)}" placeholder="{placeholder}"{disabled}></label>'
        )
    if kind == "textarea":
        return (
            f'<label class="specimen-field"{style_attr}><span>{label}</span>'
            f'<textarea placeholder="{placeholder}"{disabled}>{esc(value)}</textarea></label>'
        )
    if kind == "switch":
        checked = " checked" if config.get("checked") else ""
        return (
            f'<label class="specimen-switch"{style_attr}><input type="checkbox" role="switch"'
            f'{checked}{disabled}><span class="switch-track"><span class="switch-thumb"></span></span>'
            f'<span>{label}</span></label>'
        )
    if kind == "slider":
        slider_value = config.get("value", specimen["value"])
        return (
            f'<label class="specimen-slider"{style_attr}><span>{label}</span>'
            f'<input type="range" min="{esc(specimen["min"])}" max="{esc(specimen["max"])}" '
            f'step="{esc(specimen["step"])}" value="{esc(slider_value)}"{disabled}>'
            f'<output>{esc(slider_value)}</output></label>'
        )
    if kind == "tabs":
        selected_index = config.get("selectedIndex", specimen.get("selectedIndex", 0))
        secondary = esc(specimen["secondaryLabel"])
        return (
            f'<div class="specimen-tabs" role="tablist"{style_attr}>'
            f'<button type="button" role="tab" aria-selected="{str(selected_index == 0).lower()}"'
            f' class="{"is-selected" if selected_index == 0 else ""}">{label}</button>'
            f'<button type="button" role="tab" aria-selected="{str(selected_index == 1).lower()}"'
            f' class="{"is-selected" if selected_index == 1 else ""}">{secondary}</button></div>'
        )
    if kind == "composer":
        action = esc(specimen.get("actionLabel", "Run"))
        tool = specimen.get("toolLabel")
        tool_control = ""
        if tool:
            selected = " is-selected" if config.get("toolsActive") else ""
            tool_control = (
                f'<button type="button" class="composer-tool{selected}">{esc(tool)}</button>'
            )
        return (
            f'<div class="specimen-composer"{style_attr}><textarea placeholder="{placeholder}"{disabled}></textarea>'
            f'<div class="composer-actions">{tool_control}<button type="button"{disabled}>{action}</button></div></div>'
        )

    description = esc(specimen.get("description", component["role"]))
    return (
        f'<div class="specimen-surface specimen-{kind}"{style_attr}>'
        f'<strong>{label}</strong><span>{description}</span></div>'
    )


def _render_component_specimen(data: dict[str, Any], component: dict[str, Any]) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    states = []
    for state, config in component["specimen"]["states"].items():
        element = _render_specimen_element(data, component, state, config)
        states.append(
            f'<div class="specimen-state" data-component-state="{esc(state)}">'
            f'<small>{esc(state)}</small>{element}</div>'
        )
    return (
        f'<div class="specimen-board" data-component="{esc(component["name"])}" '
        f'data-kind="{esc(component["specimen"]["kind"])}">{"".join(states)}</div>'
    )


def render_preview(data: dict[str, Any], declarations: list[str], site_slug: str) -> str:
    meta = data["meta"]
    ext = data["$extensions"][EXTENSION_KEY]
    coverage = ext["coverage"]
    esc = lambda value: html.escape(str(value), quote=True)

    color_cards = []
    for name, token in data["color"].items():
        value = _display_value(data, "color", name)
        color_cards.append(
            f'<article class="swatch"><div class="swatch-color" style="background:{esc(value)}"></div>'
            f'<div class="swatch-copy"><strong>{esc(name)}</strong><code>{esc(value)}</code>'
            f'<p>{esc(token["$description"])}</p></div></article>'
        )

    type_rows = []
    for name, token in data["typography"].items():
        value = resolve_value(data, "typography", name)
        style = (
            f"font-family:{value['fontFamily']};font-size:{value['fontSize']};"
            f"font-weight:{value['fontWeight']};line-height:{value['lineHeight']};"
            f"letter-spacing:{value['letterSpacing']}"
        )
        type_rows.append(
            f'<div class="type-row"><code>{esc(name)}</code><span style="{esc(style)}">'
            f'{esc(meta["name"])} — {esc(name)}</span><small>{esc(_display_value(data, "typography", name))}</small></div>'
        )

    spacing_items = []
    for name in data["spacing"]:
        value = _display_value(data, "spacing", name)
        spacing_items.append(
            f'<div class="measure"><div class="bar" style="height:{_visual_height(value)}px"></div>'
            f'<strong>{esc(name)}</strong><code>{esc(value)}</code></div>'
        )

    radius_items = []
    for name in data["radius"]:
        value = _display_value(data, "radius", name)
        radius_items.append(
            f'<div class="measure"><div class="shape" style="border-radius:{esc(value)}"></div>'
            f'<strong>{esc(name)}</strong><code>{esc(value)}</code></div>'
        )

    shadow_items = []
    for name, token in data.get("shadow", {}).items():
        value = _display_value(data, "shadow", name)
        shadow_items.append(
            f'<div class="shadow-card" style="box-shadow:{esc(value)}"><strong>{esc(name)}</strong>'
            f'<code>{esc(value)}</code><p>{esc(token["$description"])}</p></div>'
        )

    component_cards = []
    for component in ext["components"]:
        specimen = _render_component_specimen(data, component)
        properties = "".join(
            f'<li><span>{esc(key)}</span><code>{esc(value)}</code></li>'
            for key, value in component["properties"].items()
        )
        states = "".join(f'<span class="tag">{esc(state)}</span>' for state in component["states"])
        component_cards.append(
            f'<article class="component"><header><div><code>{esc(component["name"])}</code>'
            f'<h3>{esc(component["role"])}</h3></div></header>{specimen}<ul>{properties}</ul>'
            f'<div class="tags">{states}</div></article>'
        )

    route_rows = "".join(
        f'<tr><td>{esc(route["family"])}</td><td><a href="{esc(route["url"])}">{esc(route["url"])}</a></td>'
        f'<td>{esc(", ".join(route["states"]))}</td></tr>'
        for route in coverage["routes"]
    )
    do_items = "".join(f"<li>{esc(item)}</li>" for item in ext.get("guidelines", {}).get("do", []))
    avoid_items = "".join(
        f"<li>{esc(item)}</li>" for item in ext.get("guidelines", {}).get("avoid", [])
    )
    gap_items = "".join(f"<li>{esc(item)}</li>" for item in coverage.get("gaps", [])) or "<li>None recorded.</li>"

    css_tokens = "\n".join(f"  {line}" for line in declarations)
    replacements = {
        "@@TITLE@@": esc(meta["name"]),
        "@@DESCRIPTION@@": esc(meta["description"]),
        "@@SOURCE@@": esc(ext["source"]["url"]),
        "@@CAPTURED@@": esc(ext["source"]["capturedAt"]),
        "@@THEME@@": esc(meta["theme"]),
        "@@DESIGN_FILE@@": esc(f"{site_slug}-DESIGN.md"),
        "@@TOKENS_FILE@@": esc(f"{site_slug}-tokens.json"),
        "@@VARIABLES_FILE@@": esc(f"{site_slug}-variables.css"),
        "@@THEME_FILE@@": esc(f"{site_slug}-theme.css"),
        "@@TOKEN_CSS@@": css_tokens,
        "@@PRIMARY@@": _pick_var(data, "color", ("primary", "accent", "brand"), "#225cff"),
        "@@ON_PRIMARY@@": _pick_var(data, "color", ("on-primary", "white", "canvas"), "#ffffff"),
        "@@CANVAS@@": _pick_var(data, "color", ("canvas", "background", "white"), "#ffffff"),
        "@@SURFACE@@": _pick_var(data, "color", ("surface-soft", "surface", "canvas"), "#f6f7fb"),
        "@@INK@@": _pick_var(data, "color", ("ink", "body", "text"), "#17181b"),
        "@@MUTED@@": _pick_var(data, "color", ("muted", "body-muted", "body"), "#6f7480"),
        "@@BORDER@@": _pick_var(data, "color", ("border", "hairline", "divider"), "#d9dce5"),
        "@@RADIUS@@": _pick_var(data, "radius", ("lg", "md", "sm"), "16px"),
        "@@COLOR_COUNT@@": str(len(data["color"])),
        "@@TYPE_COUNT@@": str(len(data["typography"])),
        "@@COMPONENT_COUNT@@": str(len(ext["components"])),
        "@@VIEWPORTS@@": esc(" · ".join(coverage["viewports"])),
        "@@COLORS@@": "".join(color_cards),
        "@@TYPE_ROWS@@": "".join(type_rows),
        "@@SPACING@@": "".join(spacing_items),
        "@@RADII@@": "".join(radius_items),
        "@@SHADOWS@@": "".join(shadow_items) or '<p class="empty">No shadow tokens recorded.</p>',
        "@@COMPONENTS@@": "".join(component_cards),
        "@@ROUTES@@": route_rows,
        "@@DO@@": do_items,
        "@@AVOID@@": avoid_items,
        "@@GAPS@@": gap_items,
    }

    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>@@TITLE@@ — Visual Token System</title>
<style>
*,*::before,*::after{box-sizing:border-box}html{scroll-behavior:smooth}
:root{
@@TOKEN_CSS@@
  --preview-primary:@@PRIMARY@@;--preview-on-primary:@@ON_PRIMARY@@;--preview-canvas:@@CANVAS@@;
  --preview-surface:@@SURFACE@@;--preview-ink:@@INK@@;--preview-muted:@@MUTED@@;
  --preview-border:@@BORDER@@;--preview-radius:@@RADIUS@@;
}
body{margin:0;background:var(--preview-canvas);color:var(--preview-ink);font-family:var(--font-primary,system-ui,sans-serif);line-height:1.5}
a{color:var(--preview-primary)}code{font:500 12px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace}
.page{width:min(1120px,calc(100% - 40px));margin:auto;padding-bottom:96px}
nav{position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:16px 0;background:color-mix(in srgb,var(--preview-canvas) 92%,transparent);backdrop-filter:blur(18px);border-bottom:1px solid var(--preview-border)}
.brand{font-weight:750}.nav-links{display:flex;gap:18px}.nav-links a{color:var(--preview-muted);font-size:13px;text-decoration:none}
.hero{padding:96px 0 72px;border-bottom:1px solid var(--preview-border)}
.eyebrow{color:var(--preview-primary);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
h1{max-width:850px;margin:14px 0 20px;font-size:clamp(42px,7vw,82px);line-height:.98;letter-spacing:-.05em}
.lede{max-width:760px;color:var(--preview-muted);font-size:clamp(17px,2.2vw,22px)}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.tag{padding:5px 10px;border:1px solid var(--preview-border);border-radius:999px;color:var(--preview-muted);font-size:11px}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}.button{padding:11px 18px;border-radius:999px;text-decoration:none;font-size:13px;font-weight:700}.button.primary{background:var(--preview-primary);color:var(--preview-on-primary)}.button.secondary{border:1px solid var(--preview-border);color:var(--preview-ink)}
section{padding:72px 0 0}.section-head{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:28px}.section-head h2{margin:0;font-size:clamp(28px,4vw,46px);line-height:1}.section-head p{margin:0;color:var(--preview-muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.swatch{overflow:hidden;border:1px solid var(--preview-border);border-radius:var(--preview-radius);background:var(--preview-canvas)}.swatch-color{height:110px;border-bottom:1px solid var(--preview-border)}.swatch-copy{padding:16px}.swatch-copy strong,.swatch-copy code{display:block}.swatch-copy code{margin-top:4px;color:var(--preview-primary)}.swatch-copy p{margin:10px 0 0;color:var(--preview-muted);font-size:12px}
.type-list{border:1px solid var(--preview-border);border-radius:var(--preview-radius);overflow:hidden}.type-row{display:grid;grid-template-columns:120px 1fr 260px;align-items:baseline;gap:18px;padding:20px;border-bottom:1px solid var(--preview-border)}.type-row:last-child{border:0}.type-row>code{color:var(--preview-primary)}.type-row small{color:var(--preview-muted);text-align:right}
.measures{display:flex;align-items:flex-end;gap:22px;min-height:150px;padding:24px;border:1px solid var(--preview-border);border-radius:var(--preview-radius);overflow:auto}.measure{min-width:72px;display:grid;justify-items:center;gap:8px}.bar{width:48px;border-radius:8px 8px 2px 2px;background:var(--preview-primary);opacity:.75}.shape{width:72px;height:72px;background:var(--preview-surface);border:2px solid var(--preview-primary)}.measure strong{font-size:12px}.measure code{color:var(--preview-muted)}
.shadow-card,.component{padding:22px;border-radius:var(--preview-radius);background:var(--preview-canvas);border:1px solid var(--preview-border)}.shadow-card code{display:block;margin-top:10px;color:var(--preview-primary);word-break:break-word}.shadow-card p{color:var(--preview-muted);font-size:12px}
.components{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px}.component h3{margin:8px 0 18px;font-size:17px}.component header code{color:var(--preview-primary)}.component ul{list-style:none;padding:0;margin:18px 0 0}.component li{display:flex;justify-content:space-between;gap:18px;padding:9px 0;border-top:1px solid var(--preview-border);font-size:12px}.component li span{color:var(--preview-muted)}.component li code{text-align:right;word-break:break-word}
.specimen-board{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;padding:16px;overflow:auto;border:1px solid var(--preview-border);border-radius:calc(var(--preview-radius) * .7);background:var(--preview-surface)}.specimen-board[data-kind="composer"]{grid-template-columns:1fr}.specimen-state{display:grid;align-content:start;justify-items:start;gap:10px;min-width:0}.specimen-state>small{color:var(--preview-muted);font:600 10px/1.2 ui-monospace,SFMono-Regular,Consolas,monospace;text-transform:uppercase;letter-spacing:.05em}.specimen-control,.specimen-tabs button,.specimen-composer button{appearance:none;border:1px solid var(--preview-border);background:var(--preview-canvas);color:var(--preview-ink);cursor:pointer}.specimen-state[data-component-state="focus-visible"] :is(button,input,textarea){outline:2px solid;outline-offset:2px}.specimen-control:disabled,.specimen-field :disabled,.specimen-switch input:disabled~*,.specimen-slider input:disabled,.specimen-composer :disabled{cursor:not-allowed;opacity:.48}.specimen-button{min-height:36px;padding:8px 14px}.specimen-icon-button{display:grid;place-items:center;width:40px;height:40px;padding:0;border-radius:50%;font-size:20px}.specimen-field{display:grid;gap:6px;width:100%;color:var(--preview-ink);font-size:12px}.specimen-field input,.specimen-field textarea{width:100%;min-height:40px;padding:9px 11px;border:1px solid var(--preview-border);border-radius:inherit;background:inherit;color:inherit;font:inherit}.specimen-field textarea{min-height:82px;resize:vertical}.specimen-switch{display:flex;align-items:center;gap:10px;cursor:pointer}.specimen-switch input{position:absolute;inline-size:1px;block-size:1px;opacity:0}.switch-track{position:relative;display:block;width:34px;height:20px;flex:0 0 auto;border-radius:999px;background:var(--spec-track,var(--preview-border));transition:background .18s ease}.switch-thumb{position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:50%;background:var(--spec-thumb,var(--preview-canvas));box-shadow:0 1px 3px #0003;transition:transform .18s ease}.specimen-switch input:checked+.switch-track{background:var(--spec-fill,var(--preview-primary))}.specimen-switch input:checked+.switch-track .switch-thumb{transform:translateX(14px)}.specimen-slider{display:grid;grid-template-columns:1fr auto;align-items:center;gap:8px;width:100%;font-size:12px}.specimen-slider>span{grid-column:1/-1}.specimen-slider input{width:100%;height:6px;margin:6px 0;appearance:none;border-radius:999px;background:linear-gradient(to right,var(--spec-fill,var(--preview-primary)) 0 var(--spec-position,50%),var(--spec-track,var(--preview-border)) var(--spec-position,50%) 100%)}.specimen-slider input::-webkit-slider-thumb{width:18px;height:18px;appearance:none;border:2px solid var(--spec-fill,var(--preview-primary));border-radius:50%;background:var(--spec-thumb,var(--preview-canvas))}.specimen-slider input::-moz-range-thumb{width:14px;height:14px;border:2px solid var(--spec-fill,var(--preview-primary));border-radius:50%;background:var(--spec-thumb,var(--preview-canvas))}.specimen-slider output{color:var(--preview-muted);font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.specimen-tabs{display:flex;gap:4px;padding:4px;border:1px solid var(--preview-border);border-radius:999px;background:var(--preview-canvas)}.specimen-tabs button{padding:7px 12px;border:0;border-radius:999px;color:var(--spec-inactive-color,var(--preview-muted))}.specimen-tabs button.is-selected{background:var(--spec-fill,var(--preview-primary));color:var(--spec-selected-color,var(--preview-on-primary))}.specimen-composer{display:grid;gap:8px;width:100%;min-width:0;padding:10px;border:1px solid var(--preview-border);border-radius:var(--preview-radius);background:var(--preview-canvas)}.specimen-composer textarea{min-height:68px;resize:vertical;border:0;outline:0;background:transparent;color:inherit;font:inherit}.composer-actions{display:flex;align-items:center;justify-content:space-between;gap:8px}.specimen-composer button{padding:8px 12px;border-radius:999px}.specimen-composer .composer-tool.is-selected{background:var(--color-selected,var(--preview-surface))}.specimen-surface{display:grid;gap:6px;width:100%;min-height:96px;padding:16px;border:1px solid var(--preview-border);border-radius:var(--preview-radius);background:var(--preview-canvas);color:var(--preview-ink)}.specimen-surface span{color:var(--preview-muted);font-size:12px}
.guides{display:grid;grid-template-columns:1fr 1fr;gap:14px}.guide{padding:24px;border:1px solid var(--preview-border);border-radius:var(--preview-radius);background:var(--preview-surface)}.guide h3{margin-top:0}.guide li{margin:10px 0;color:var(--preview-muted)}
.table-wrap{overflow:auto;border:1px solid var(--preview-border);border-radius:var(--preview-radius)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:14px;text-align:left;border-bottom:1px solid var(--preview-border)}th{color:var(--preview-muted);font-size:11px;text-transform:uppercase;letter-spacing:.05em}td a{white-space:nowrap}.gaps{color:var(--preview-muted)}.empty{color:var(--preview-muted)}
footer{margin-top:80px;padding-top:24px;border-top:1px solid var(--preview-border);color:var(--preview-muted);font-size:12px}
@media(max-width:760px){.page{width:min(100% - 28px,1120px)}.nav-links{display:none}.hero{padding:64px 0 52px}.section-head{grid-template-columns:1fr}.type-row{grid-template-columns:90px 1fr}.type-row small{display:none}.guides{grid-template-columns:1fr}.components{grid-template-columns:1fr}.specimen-board{grid-template-columns:minmax(150px,1fr)}}
</style>
</head>
<body><main class="page">
<nav><div class="brand">@@TITLE@@ <span class="tag">@@THEME@@</span></div><div class="nav-links"><a href="#colors">Colors</a><a href="#type">Type</a><a href="#components">Components</a><a href="#coverage">Coverage</a></div></nav>
<header class="hero"><div class="eyebrow">Visual token system · captured @@CAPTURED@@</div><h1>@@TITLE@@</h1><p class="lede">@@DESCRIPTION@@</p><div class="tags"><span class="tag">@@COLOR_COUNT@@ colors</span><span class="tag">@@TYPE_COUNT@@ type styles</span><span class="tag">@@COMPONENT_COUNT@@ components</span><span class="tag">@@VIEWPORTS@@</span></div><div class="actions"><a class="button primary" href="@@DESIGN_FILE@@" download>Download spec</a><a class="button secondary" href="@@TOKENS_FILE@@" download>tokens.json</a><a class="button secondary" href="@@VARIABLES_FILE@@" download>variables.css</a><a class="button secondary" href="@@THEME_FILE@@" download>theme.css</a></div></header>
<section id="colors"><div class="section-head"><h2>Color system</h2><p>Resolved semantic tokens. Aliases share one primitive value without erasing their distinct roles.</p></div><div class="grid">@@COLORS@@</div></section>
<section id="type"><div class="section-head"><h2>Typography</h2><p>Observed family, size, weight, line height and tracking rendered together.</p></div><div class="type-list">@@TYPE_ROWS@@</div></section>
<section><div class="section-head"><h2>Spacing</h2><p>The measured rhythm behind controls, cards and sections.</p></div><div class="measures">@@SPACING@@</div></section>
<section><div class="section-head"><h2>Shape</h2><p>Corner language from compact controls through feature surfaces.</p></div><div class="measures">@@RADII@@</div></section>
<section><div class="section-head"><h2>Depth</h2><p>Elevation values captured from the source experience.</p></div><div class="grid">@@SHADOWS@@</div></section>
<section id="components"><div class="section-head"><h2>Component specimens</h2><p>Native controls and structural samples rendered from the captured properties for each observed state.</p></div><div class="components">@@COMPONENTS@@</div></section>
<section><div class="section-head"><h2>Usage guidance</h2><p>Rules inferred from repeated decisions across the sampled experience.</p></div><div class="guides"><article class="guide"><h3>Do</h3><ul>@@DO@@</ul></article><article class="guide"><h3>Avoid</h3><ul>@@AVOID@@</ul></article></div></section>
<section id="coverage"><div class="section-head"><h2>Coverage</h2><p>This is a timestamped snapshot, not a claim that inaccessible product states were observed.</p></div><div class="table-wrap"><table><thead><tr><th>Page family</th><th>URL</th><th>States checked</th></tr></thead><tbody>@@ROUTES@@</tbody></table></div><h3>Known gaps</h3><ul class="gaps">@@GAPS@@</ul></section>
<footer>Source: <a href="@@SOURCE@@">@@SOURCE@@</a> · Captured @@CAPTURED@@ · Validate implementation decisions against the current live source.</footer>
</main></body></html>
"""
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def build(
    token_path: Path, output_dir: Path, slug: str | None, force: bool, check_only: bool
) -> list[Path]:
    try:
        raw = json.loads(token_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"Token source does not exist: {token_path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    data, removed = normalize(raw)
    validate(data)
    site_slug = slug or _slugify(data["meta"]["name"])
    if not NAME_RE.fullmatch(site_slug):
        raise ContractError("--slug must use lowercase kebab-case.")

    if check_only:
        print(f"OK: contract valid; {removed} duplicate observation(s) normalized in memory.")
        return []

    declarations = css_declarations(data)
    token_json = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    design_md = render_design_md(data)
    variables_css = render_css(data, ":root", "design tokens")
    theme_css = render_css(data, "@theme", "Tailwind CSS v4 theme")
    preview_html = render_preview(data, declarations, site_slug)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "design": output_dir / f"{site_slug}-DESIGN.md",
        "tokens": output_dir / f"{site_slug}-tokens.json",
        "variables": output_dir / f"{site_slug}-variables.css",
        "theme": output_dir / f"{site_slug}-theme.css",
        "preview": output_dir / f"{site_slug}-preview.html",
    }
    source_path = token_path.resolve()
    conflicts = [
        path
        for path in paths.values()
        if path.exists() and not (path.resolve() == source_path and path == paths["tokens"])
    ]
    if conflicts and not force:
        rendered = "\n".join(f"- {path}" for path in conflicts)
        raise ContractError(f"Refusing to overwrite existing generated files:\n{rendered}\nUse --force after verifying them.")

    _write_text(paths["design"], design_md)
    _write_text(paths["tokens"], token_json)
    _write_text(paths["variables"], variables_css)
    _write_text(paths["theme"], theme_css)
    _write_text(paths["preview"], preview_html)

    empty = [path for path in paths.values() if not path.is_file() or path.stat().st_size == 0]
    if empty:
        raise ContractError(f"Generated empty artifacts: {[str(path) for path in empty]}.")

    print(f"OK: generated {len(paths)} files; removed {removed} duplicate observation(s).")
    for path in paths.values():
        print(path)
    return list(paths.values())


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a UI/UX token source and build the five visual-token artifacts."
    )
    parser.add_argument("tokens", type=Path, help="Path to the single-source tokens JSON.")
    parser.add_argument("--output-dir", type=Path, help="Output directory; defaults to the token file directory.")
    parser.add_argument("--slug", help="ASCII kebab-case output prefix; defaults to meta.name.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files.")
    parser.add_argument("--check-only", action="store_true", help="Validate and normalize in memory without writing files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_dir = args.output_dir or args.tokens.parent
    try:
        build(args.tokens, output_dir, args.slug, args.force, args.check_only)
    except (ContractError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

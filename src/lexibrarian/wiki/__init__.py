"""Wiki module — concept file parser, serializer, template, and resolver utilities."""

from __future__ import annotations

from lexibrarian.wiki.index import ConceptIndex
from lexibrarian.wiki.parser import parse_concept_file
from lexibrarian.wiki.resolver import ResolvedLink, UnresolvedLink, WikilinkResolver
from lexibrarian.wiki.serializer import serialize_concept_file
from lexibrarian.wiki.template import concept_file_path, render_concept_template

__all__ = [
    "ConceptIndex",
    "ResolvedLink",
    "UnresolvedLink",
    "WikilinkResolver",
    "parse_concept_file",
    "serialize_concept_file",
    "render_concept_template",
    "concept_file_path",
]

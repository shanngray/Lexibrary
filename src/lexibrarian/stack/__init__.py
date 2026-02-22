"""Stack module — Stack Overflow-style Q&A knowledge base for Lexibrarian."""

from __future__ import annotations

from lexibrarian.stack.index import StackIndex
from lexibrarian.stack.models import (
    StackAnswer,
    StackPost,
    StackPostFrontmatter,
    StackPostRefs,
)
from lexibrarian.stack.mutations import (
    accept_answer,
    add_answer,
    mark_duplicate,
    mark_outdated,
    record_vote,
)
from lexibrarian.stack.parser import parse_stack_post
from lexibrarian.stack.serializer import serialize_stack_post
from lexibrarian.stack.template import render_post_template

__all__ = [
    "StackAnswer",
    "StackIndex",
    "StackPost",
    "StackPostFrontmatter",
    "StackPostRefs",
    "accept_answer",
    "add_answer",
    "mark_duplicate",
    "mark_outdated",
    "parse_stack_post",
    "record_vote",
    "render_post_template",
    "serialize_stack_post",
]

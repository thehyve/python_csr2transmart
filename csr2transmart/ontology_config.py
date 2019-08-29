from typing import Sequence, Optional

from pydantic import BaseModel


class TreeNode(BaseModel):
    """
    Ontology node
    """
    name: str
    children: Optional[Sequence['TreeNode']]


class ConceptNode(TreeNode):
    """
    Concept ontology node
    """
    concept_code: str


class OntologyConfig(BaseModel):
    """
    Ontology tree configuration
    """
    nodes: Sequence[TreeNode]

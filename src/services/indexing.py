"""The indexing service: embeds and stores the vectors after a change (D-13, D-27).

A caller embeds first, then writes its records, then saves the vectors. When the embedding model
does not answer, the embedder raises EmbeddingUnavailable before any record is written.
"""

import logging
from typing import Dict, List, Optional, Tuple

from src.domain import skill_tree, vector_text
from src.domain.models import (
    Assignment,
    AssignmentVector,
    EmbeddingUnavailable,
    Engineer,
    Node,
    ProfileVector,
    Project,
)

logger = logging.getLogger(__name__)

MODEL_KEY = "embedding_model"
VECTOR_SIZE_KEY = "vector_size"


class IndexingService:
    """Embeds the texts of assignments and profiles and keeps the vector tables current."""

    def __init__(self, store, embedder):
        """Use store (a LanceStore or a fake) and embedder (OllamaEmbedder or a fake)."""
        self._store = store
        self._embedder = embedder

    def embed_assignments(
        self,
        assignments: List[Assignment],
        project: Optional[Project] = None,
        nodes: Optional[List[Node]] = None,
    ) -> List[AssignmentVector]:
        """Embed the assignments whose text differs from the stored one, and return their vectors.

        project and nodes hold values that are not written yet: project replaces the stored
        project with the same ID, and nodes replaces the stored tree.
        """
        projects = {p.id: p for p in self._store.list_projects()}
        if project is not None:
            projects[project.id] = project
        tree = nodes if nodes is not None else self._store.list_nodes()
        stored = {v.assignment_id: v.text for v in self._store.list_assignment_vectors()}
        pending = [
            (assignment, text)
            for assignment, text in self._assignment_texts(assignments, projects, tree)
            if stored.get(assignment.id) != text
        ]
        return self._embed_assignment_texts(pending)

    def save_assignment_vectors(self, vectors: List[AssignmentVector]) -> None:
        """Write the vectors that embed_assignments returned."""
        self._store.save_assignment_vectors(vectors)

    def delete_assignment_vectors(self, assignment_ids: List[str]) -> None:
        """Delete the vectors of deleted assignments."""
        self._store.delete_assignment_vectors(assignment_ids)

    def embed_profile(self, engineer: Engineer) -> Optional[ProfileVector]:
        """Embed the skill gaps when they are not empty and differ from the stored text (D-27)."""
        text = vector_text.profile_text(engineer)
        stored = {v.engineer_id: v.text for v in self._store.list_profile_vectors()}
        if not text or stored.get(engineer.id) == text:
            return None
        return ProfileVector(engineer.id, text, self._embedder.embed([text])[0])

    def save_profile(self, engineer: Engineer, vector: Optional[ProfileVector]) -> None:
        """Write the vector that embed_profile returned; empty skill gaps remove the vector."""
        if vector is not None:
            self._store.save_profile_vector(vector)
        elif not vector_text.profile_text(engineer):
            self._store.delete_profile_vector(engineer.id)

    def delete_engineer_vectors(self, engineer_id: str) -> None:
        """Delete the assignment vectors and the profile vector of a deleted engineer."""
        self._store.delete_assignment_vectors_of_engineer(engineer_id)
        self._store.delete_profile_vector(engineer_id)

    def sync_model(self) -> None:
        """Embed all vectors again when the model or the vector size in meta differs (D-27).

        When the model does not answer, log it and keep the vectors; the next start tries again.
        """
        try:
            wanted = {
                MODEL_KEY: self._embedder.model_name,
                VECTOR_SIZE_KEY: str(self._embedder.vector_size),
            }
            meta = self._store.get_meta()
            if all(meta.get(key) == value for key, value in wanted.items()):
                return
            self._embed_everything()
            self._store.set_meta(wanted)
            logger.info("Embedded all vectors with the current embedding model.")
        except EmbeddingUnavailable:
            logger.warning("The embedding model does not answer; the vectors were not checked.")

    def _embed_everything(self) -> None:
        """Embed every assignment and every profile, then replace both vector tables."""
        projects = {p.id: p for p in self._store.list_projects()}
        pending = self._assignment_texts(
            self._store.list_assignments(), projects, self._store.list_nodes()
        )
        assignment_vectors = self._embed_assignment_texts(pending)
        profiles = [
            (e.id, vector_text.profile_text(e))
            for e in self._store.list_engineers()
            if vector_text.profile_text(e)
        ]
        profile_vectors = self._embed([text for _id, text in profiles])
        self._store.drop_vectors()
        self._store.save_assignment_vectors(assignment_vectors)
        for (engineer_id, text), vector in zip(profiles, profile_vectors):
            self._store.save_profile_vector(ProfileVector(engineer_id, text, vector))

    def _assignment_texts(
        self, assignments: List[Assignment], projects: Dict[str, Project], nodes: List[Node]
    ) -> List[Tuple[Assignment, str]]:
        """Return each assignment with its vector text; skip one whose project or leaf is gone."""
        by_id = {n.id: n for n in nodes}
        result = []
        for assignment in assignments:
            project = projects.get(assignment.project_id)
            leaf = by_id.get(assignment.leaf_id)
            if project is None or leaf is None:
                logger.warning("Skipped the vector of an assignment with no project or leaf.")
                continue
            leaf_path = skill_tree.path(nodes, leaf.id)
            text = vector_text.assignment_text(assignment, project, leaf, leaf_path)
            result.append((assignment, text))
        return result

    def _embed_assignment_texts(
        self, pending: List[Tuple[Assignment, str]]
    ) -> List[AssignmentVector]:
        """Embed the texts in one call and return one AssignmentVector for each assignment."""
        vectors = self._embed([text for _assignment, text in pending])
        return [
            AssignmentVector(assignment.id, assignment.engineer_id, text, vector)
            for (assignment, text), vector in zip(pending, vectors)
        ]

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Return the vectors of the texts; no text makes no call to the embedder."""
        if not texts:
            return []
        return self._embedder.embed(texts)

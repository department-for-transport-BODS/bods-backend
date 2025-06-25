"""
Utils module for track consolidation logic
"""

from collections import defaultdict

from aws_lambda_powertools import Tracer
from common_layer.database.models import TransmodelTracks
from structlog.stdlib import get_logger

tracer = Tracer()
log = get_logger()


def choose_canonical_track(similar_tracks: list[TransmodelTracks]) -> TransmodelTracks:
    """
    Choose a canonical track from a list of tracks we consider to be the same
    """
    return min(similar_tracks, key=lambda t: t.id)


def find_root(parents: dict[int, int], x: int) -> tuple[int, dict[int, int]]:
    """
    Follows the chain of parent links to find the root item for the item x.

    Each item belongs to a group, and the root is the item that represents that group.

    For example, given:
        parents = {2: 1, 3: 2, 4: 3}
        find(parents, 4) returns (1, updated_parents)
    So item 4 belongs to a group with root 1 (e.g. track with id 1)
    """
    path: list[int] = []
    while x in parents and parents[x] != x:
        path.append(x)
        x = parents[x]
    root = x

    # Make all nodes point to the root node
    # This makes subsequent lookups faster
    for node in path:
        parents = {**parents, node: root}

    return root, parents


def union(parents: dict[int, int], x: int, y: int) -> dict[int, int]:
    """
    Join the group containing x with the group containing y.

    Find the root item for both x and y, then connect the tree containing y
    to the root of the tree containing x, merging the two groups into one.

    Returns a new parents dictionary with the updated links.

    Example:
        parents = {2: 1, 3: 2, 5: 4}
        union(parents, 3, 5)  # joins groups [1,2,3] and [4,5]

        Resulting parents:
        {2: 1, 3: 2, 5: 4, 4: 1}  # 4 now points to 1, merging the trees
    """
    root_x, parents = find_root(parents, x)
    root_y, parents = find_root(parents, y)

    if root_x != root_y:
        parents = {**parents, root_y: root_x}
    return parents


def build_duplicate_groups(
    pairs_of_duplicate_tracks: list[tuple[int, int]],
) -> list[set[int]]:
    """
    Given a list of (track_a, track_b) similar track pairs, return a list of sets representing
    duplicate track groups.

    Example:
    track_pairs = [
        (track1, track2),
        (track2, track3),
        (track4, track5)
    ]

    result = [
        {track1, track2, track3},
        {track4, track5}
    ]
    """
    parents: dict[int, int] = {}

    for track_a, track_b in pairs_of_duplicate_tracks:
        parents = {
            **parents,
            track_a: parents.get(track_a, track_a),
            track_b: parents.get(track_b, track_b),
        }
        # Join the groups for track_a and track_b
        # (since they're duplicates, they should be in the same group)
        parents = union(parents, track_a, track_b)

    groups: dict[int, set[int]] = defaultdict(set)
    for track_id in parents:
        # Find the group that this track_id belongs to
        root, parents = find_root(parents, track_id)
        # Add the track to the group it belongs to
        groups[root].add(track_id)

    return list(groups.values())

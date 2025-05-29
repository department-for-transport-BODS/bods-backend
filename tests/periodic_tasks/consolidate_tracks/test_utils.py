import pytest

from periodic_tasks.consolidate_tracks.app.utils import build_duplicate_groups, union


@pytest.mark.parametrize(
    "similar_track_pairs, expected_result",
    [
        pytest.param(
            [
                (
                    1,
                    2,
                ),
                (
                    2,
                    3,
                ),
            ],
            [{1, 2, 3}],
            id="Three pairs, one group",
        ),
        pytest.param(
            [
                (
                    1,
                    2,
                ),
                (
                    2,
                    3,
                ),
                (
                    4,
                    5,
                ),
            ],
            [{1, 2, 3}, {4, 5}],
            id="Multiple groups",
        ),
        pytest.param(
            [],
            [],
            id="No pairs",
        ),
    ],
)
def test_build_duplicate_groups(
    similar_track_pairs: list[tuple[int, int]], expected_result: list[set[int]]
) -> None:
    assert build_duplicate_groups(similar_track_pairs) == expected_result


@pytest.mark.parametrize(
    "parents, x, y, expected_result",
    [
        pytest.param(
            {},  # no links yet
            1,
            2,
            {2: 1},  # One tree (2 -> 1)
            id="Two singletons",
        ),
        pytest.param(
            {2: 1, 4: 3},  # Two unconnected trees (2 -> 1) and (4 -> 3)
            2,
            4,
            {2: 1, 4: 3, 3: 1},  # Single tree with 2 branches (4 -> 3 -> 1), (2 -> 1)
            id="Merge two flat trees",
        ),
        pytest.param(
            {2: 1, 3: 2},  # One tree (3 -> 2 -> 1)
            1,
            3,
            {2: 1, 3: 1},  # Same tree, 1 and 3 are already connected
            id="Merge already connected trees",
        ),
        pytest.param(
            {2: 1, 3: 2, 5: 4},  # Two unconnected trees: (3 -> 2 -> 1) and (5 -> 4)
            3,
            5,
            {
                2: 1,
                3: 1,  # 3 now linked directly to root ("path compression")
                5: 4,
                4: 1,  # (5 -> 4) subtree gets attached to 1 (5 -> 4 -> 1)
            },  # One merged tree with flattened links
            id="Merge deeper tree: path compression",
        ),
    ],
)
def test_union(
    parents: dict[int, int], x: int, y: int, expected_result: dict[int, int]
) -> None:
    assert union(parents, x, y) == expected_result

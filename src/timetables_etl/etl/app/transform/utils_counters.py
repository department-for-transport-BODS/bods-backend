"""
Functions that get the counts 
"""

from common_layer.txc.models import TXCJourneyPatternSection


def count_principle_timing_points(jps_list: list[TXCJourneyPatternSection]) -> int:
    """
    Count the number of principle timing points across a list of Journey Pattern Sections
    """
    count: int = 0
    for jps in jps_list:
        for jptl in jps.JourneyPatternTimingLink:
            if jptl.From.TimingStatus == "principalTimingPoint":
                count += 1
            if jptl.To.TimingStatus == "principalTimingPoint":
                count += 1
    return count

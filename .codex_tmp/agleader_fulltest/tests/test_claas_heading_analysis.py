from exportar_rindes.readers.claas.analysis import (
    HeadingEvidence,
    circular_error_deg,
    segment_bearing_deg,
)


def test_claas_heading_candidate_matches_cardinal_segments() -> None:
    north, distance_north = segment_bearing_deg(41.0, -5.0, 41.001, -5.0)
    east, distance_east = segment_bearing_deg(41.0, -5.0, 41.0, -4.999)
    assert north == 0
    assert round(east, 6) == 90
    assert distance_north > 100
    assert distance_east > 80
    assert circular_error_deg(359, 1) == 2


def test_claas_heading_evidence_reports_thresholds() -> None:
    evidence = HeadingEvidence()
    evidence.add(41.0, -5.0, 41.001, -5.0, 1)
    evidence.add(41.0, -5.0, 41.0, -4.999, 100)
    report = evidence.report()
    assert report["segment_count"] == 2
    assert report["within_5_deg_pct"] == 50
    assert report["within_15_deg_pct"] == 100

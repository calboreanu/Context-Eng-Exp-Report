#!/usr/bin/env python3
"""Render Figure 4 with an explicitly historical author-check note.

The versioned analysis renderer supplies the current numerical figure. This
display-only adapter replaces its identified subtitle, not any numerical value.
"""
import argparse
import json
from pathlib import Path
import runpy
import sys

OLD_SUBTITLE = 'balanced cohorts and a separate candidate-linkage pilot; every label is automated and unadjudicated'


def reviewed_subtitle(summary):
    if (summary['selected_events'], summary['author_reported_reviewed_events'],
        summary['collectively_confirmed_classifications'], summary['inaccuracies_reported']) != (46, 46, 46, 0):
        raise ValueError('This display adapter is bound to the recorded 46-case confirmation')
    if summary['review_design'] != 'author_involved_unblinded_collective_confirmation':
        raise ValueError('Unexpected review design')
    if summary.get('reviewed_analysis_version') != 'event-v3':
        raise ValueError('The recorded author check must remain bound to event-v3')
    if summary.get('applies_to_entire_corrected_analysis') is not False:
        raise ValueError('Do not transfer the historical check to the corrected analysis')
    return 'historical 46-case author check; candidate linkage remains unadjudicated'


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=root / 'outputs/figures')
    args = parser.parse_args()
    scripts = root / 'analysis/scripts'
    summary = json.loads((root / 'data/validation/author_review_summary.json').read_text())
    subtitle = reviewed_subtitle(summary)
    previous_argv = sys.argv[:]
    sys.path.insert(0, str(scripts))
    try:
        sys.argv = [str(scripts / 'gen_fig06_house.py'),
                    '--analysis-summary', str(root / 'analysis/results/analysis_summary.json'),
                    '--inheritance-summary', str(root / 'analysis/results/inheritance_pilot_summary.json'),
                    '--output-dir', str(args.output_dir)]
        result = runpy.run_path(str(scripts / 'gen_fig06_house.py'), run_name='__main__')
    finally:
        sys.argv = previous_argv
        sys.path.pop(0)
    fig, ax = result['fig'], result['ax']
    texts_before = [text.get_text() for text in ax.texts]
    matches = [text for text in ax.texts if text.get_text() == OLD_SUBTITLE]
    if len(matches) != 1:
        raise ValueError('Frozen renderer subtitle not found exactly once')
    matches[0].set_text(subtitle)
    texts_after = [text.get_text() for text in ax.texts]
    assert sum(a != b for a, b in zip(texts_before, texts_after)) == 1
    fig.savefig(args.output_dir / 'fig-06-analysis-evidence-map.pdf', facecolor='white')
    print('Updated only the review-status subtitle; all numerical figure text is unchanged.')


if __name__ == '__main__':
    main()

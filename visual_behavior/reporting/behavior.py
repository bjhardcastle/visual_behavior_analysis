from ..translator.core import create_extended_dataframe
from ..change_detection.trials.summarize import DEFAULT_SUMMARY_METRICS


def change_detection_metrics(core_data):

    trials = create_extended_dataframe(
        trials=core_data['trials'],
        metadata=core_data['metadata'],
        licks=core_data['licks'],
        time=core_data['time'],
    )

    summary_metrics = DEFAULT_SUMMARY_METRICS.copy()

    summary = {
        metric: func(trials)
        for metric, func
        in summary_metrics.items()
    }

    return summary

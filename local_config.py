tool_name = 'ml'
report_type = 'perf'
show_skipped_groups = True
tracked_metrics = {
    'test_status': {'metric_name': 'passed', 'displaying_name': 'Passed tests number', 'function': 'match', 'pattern': 'passed', 'displaying_unit': '', 'separation_field': 'tool', 'display_zeros': True},
    'render_time': {'displaying_name': 'Render time', 'function': 'sum', 'displaying_unit': 's', 'separation_field': 'tool'}
}
tracked_metrics_files_number = 10000
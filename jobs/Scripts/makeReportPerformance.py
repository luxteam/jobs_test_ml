import argparse
import os
import json
import sys
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from jobs_launcher.core.config import TEST_REPORT_NAME_COMPARED, CASE_REPORT_SUFFIX


def generate_report(directory):
    files = os.listdir(directory)
            
    json_files = list(filter(lambda x: x.endswith('RPR.json'), files))
    result_json = []

    render_logs_path = os.path.join(directory, 'render_tool_logs')

    for file in json_files:
        with open(os.path.join(render_logs_path, file), 'r') as json_report:
            data = json.load(json_report)[0]

        log_name = file.replace(CASE_REPORT_SUFFIX, '.log')
        time = None
        lines = []
        lines.append('--- {} ---'.format(log_name))
        with open(os.path.join(render_logs_path, log_name), 'r') as log_file:
            log = log_file.readlines()
            is_gpu_section = False
            for line in log:
                lines.append(line)
                if 'rml' in log_name:
                    if 'Inference time' in line:
                        time = float(line.split(':')[1].replace('ms', ''))
                elif 'winml' in log_name:
                    if 'device = GPU' in line:
                        is_gpu_section = True
                    if is_gpu_section and 'Evaluate' in line:
                        time = float(line.split(':')[1].replace('ms', ''))
                elif 'tensorrt' in log_name:
                    if 'GPU Compute' in line:
                        is_gpu_section = True
                    if is_gpu_section and 'mean' in line:
                        time = float(line.split(':')[1].replace('ms', ''))
        lines.append('')
        with open(os.path.join(directory, 'renderTool.log'), 'a') as log_file:
            log.file.writelines(lines)
        if time is None:
            data['test_status'] = 'error'
        else:
            data['render_time'] = time

        result_json.append(data)

    with open(os.path.join(directory, TEST_REPORT_NAME_COMPARED), 'w') as file:
        json.dump(result_json, file, indent=4)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--work_dir', required=True)
    args = parser.parse_args()

    generate_report(args.work_dir)

import argparse
import os
import subprocess
import psutil
import json
import platform
from datetime import datetime
from shutil import copyfile, move, which
import sys
from utils import is_case_skipped

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
import jobs_launcher.core.config as core_config
from jobs_launcher.core.system_info import get_gpu


def createArgsParser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--rmlTool', metavar='<rml_path>')
    parser.add_argument('--winmlTool', metavar='<winml_path>')
    parser.add_argument('--tensorrtTool', metavar='<tensorrt_path>')
    parser.add_argument('--output', required=True, metavar='<output_dir>')
    parser.add_argument('--testType', required=True)
    parser.add_argument('--res_path', required=True)
    parser.add_argument('--data_path', required=True)
    parser.add_argument('--testCases', required=True)
    parser.add_argument('--timeout', required=False, default=120)

    return parser


def execute_case(args, case, tool, cmd_script, cmd_script_path):
    try:
        with open(cmd_script_path, 'w') as f:
            f.write(cmd_script)

        if platform.system() != 'Windows':
            os.system('chmod +x {}'.format(cmd_script_path))

    except OSError as err:
        core_config.main_logger.error('Can\'t save run scripts: {}'.format(str(err)))

    status = 'error'

    os.chdir(args.output)
    p = psutil.Popen(cmd_script_path, shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        stdout, stderr = p.communicate(timeout=float(args.timeout))
        status = 'passed'
    except (psutil.TimeoutExpired, subprocess.TimeoutExpired) as err:
        core_config.main_logger.error('Test case has been aborted by timeout')
        for child in reversed(p.children(recursive=True)):
            child.terminate()
        p.terminate()
    finally:
        status_name = 'test_status_{}'.format(tool)
        with open(os.path.join(args.output, case['case'] + core_config.CASE_REPORT_SUFFIX), 'r') as f:
            report = json.load(f)

        with open('{}_{}.log'.format(case['case'].replace(', ', '_').replace(' ', '_'), tool), 'w', encoding='utf-8') as file:
            stdout = stdout.decode('utf-8')
            file.write(stdout)
            file.write('\n ----STEDERR---- \n')
            stderr = stderr.decode('utf-8')
            file.write(stderr)

        if status_name != 'skipped':
            report[0][status_name] = status
            with open(os.path.join(args.output, case['case'] + core_config.CASE_REPORT_SUFFIX), 'w') as f:
                json.dump(report, f, indent=4)


if __name__ == '__main__':
    core_config.main_logger.info('measurePerformance start working...')

    args = createArgsParser().parse_args()

    try:
        os.makedirs(args.output)
    except OSError as e:
        pass

    try:
        copyfile(os.path.realpath(os.path.join(os.path.dirname(
            __file__), '..', 'Tests', args.testType, 'test_cases.json')),
            os.path.realpath(os.path.join(os.path.abspath(
                args.output), 'test_cases.json')))
    except:
        core_config.logging.error('Can\'t copy test_cases.json')
        core_config.main_logger.error(str(e))
        exit(-1)

    core_config.main_logger.info('Make "base_functions.py"')

    try:
        cases = json.load(open(os.path.realpath(
            os.path.join(os.path.abspath(args.output), 'test_cases.json'))))
    except Exception as e:
        core_config.logging.error('Can\'t load test_cases.json')
        core_config.main_logger.error(str(e))
        group_failed(args)
        exit(-1)

    gpu = get_gpu()
    if not gpu:
        core_config.main_logger.error("Can't get gpu name")
    render_platform = {platform.system(), gpu}

    for case in cases:
        if is_case_skipped(case, render_platform):
            case['status'] = 'skipped'

        template = {}
        template['test_case'] = case['case']
        template['render_device'] = get_gpu()
        template['onnx'] = case['onnx']
        template['onnx'] = case['bin']
        template['onnx'] = case['csv']
        template['test_group'] = args.testType
        template['date_time'] = datetime.now().strftime(
            '%m/%d/%Y %H:%M:%S')
        if case['status'] == 'skipped':
            if args.rmlTool:
                template['test_status_rml'] = 'skipped'
            if args.winmlTool:
                template['test_status_winml'] = 'skipped'
            if args.tensorrtTool:
                template['test_status_tensorrt'] = 'skipped'
        else:
            if args.rmlTool:
                template['test_status_rml'] = 'error'
            if args.winmlTool:
                template['test_status_winml'] = 'error'
            if args.tensorrtTool:
                template['test_status_tensorrt'] = 'error'

        with open(os.path.join(args.output, case['case'] + core_config.CASE_REPORT_SUFFIX), 'w') as f:
            f.write(json.dumps([template], indent=4))

    if args.rmlTool:
        args.rmlTool = os.path.abspath(args.rmlTool)

    for case in cases:
        onnx_path = os.path.join(args.res_path, case['onnx']).replace('/', os.path.sep)
        csv_path = os.path.join(args.data_path, case['csv']).replace('/', os.path.sep)
        bin_path = os.path.join(args.data_path, case['bin']).replace('/', os.path.sep)

        if args.rmlTool:
            cmd_line = case['cmd_line_rml']
            cmd_script = cmd_line.format(tool_path=args.rmlTool, onnx_path=onnx_path, bin_path=bin_path)
            cmd_script_path = os.path.join(args.output, '{}_rml.bat'.format(case['case'].replace(', ', '_').replace(' ', '_')))
            execute_case(args, case, 'rml', cmd_script, cmd_script_path)
        if args.winmlTool:
            cmd_line = case['cmd_line_winml']
            cmd_script = cmd_line.format(tool_path=args.winmlTool, onnx_path=onnx_path, csv_path=csv_path)
            cmd_script_path = os.path.join(args.output, '{}winml.bat'.format(case['case'].replace(', ', '_').replace(' ', '_')))
            execute_case(args, case, 'winml', cmd_script, cmd_script_path)
        if args.tensorrtTool:
            cmd_line = case['cmd_line_tensorrt']
            cmd_script = cmd_line.format(tool_path=args.tensorrtTool, onnx_path=onnx_path, csv_path=csv_path)
            cmd_script_path = os.path.join(args.output, '{}tensorrt.bat'.format(case['case'].replace(', ', '_').replace(' ', '_')))
            execute_case(args, case, 'tensorrt', cmd_script, cmd_script_path)

    exit(0)
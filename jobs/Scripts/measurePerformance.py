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
from queue import Queue
from subprocess import PIPE, Popen
from threading import Thread

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
import jobs_launcher.core.config as core_config
from jobs_launcher.core.system_info import get_gpu


def createArgsParser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--rmlTool', required=True, metavar='<rml_path>')
    parser.add_argument('--winmlTool', required=True, metavar='<winml_path>')
    parser.add_argument('--tensorrtTool', required=True, metavar='<tensorrt_path>')
    parser.add_argument('--output', required=True, metavar='<output_dir>')
    parser.add_argument('--testType', required=True)
    parser.add_argument('--res_path', required=True)
    parser.add_argument('--data_path', required=True)
    parser.add_argument('--testCases', required=True)
    parser.add_argument('--timeout', required=False, default=300)

    return parser


def read_output(pipe, functions):
    for line in iter(pipe.readline, b''):
        for function in functions:
            function(line.decode('utf-8'))
    pipe.close()


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

    outs = []
    errs = []
    queue = Queue()

    stdout_thread = Thread(target=read_output, args=(p.stdout, [queue.put, outs.append]))
    stderr_thread = Thread(target=read_output, args=(p.stderr, [queue.put, errs.append]))

    for thread in (stdout_thread, stderr_thread):
        thread.daemon = True
        thread.start()

    try:
        p.wait(timeout=args.timeout)
        status = 'passed'
    except (psutil.TimeoutExpired, subprocess.TimeoutExpired) as err:
        core_config.main_logger.error('Test case {} has been aborted by timeout'.format(case['case']))
        for child in reversed(p.children(recursive=True)):
            child.terminate()
        p.terminate()
    finally:
        for thread in (stdout_thread, stderr_thread):
            thread.join()
        queue.put(None)

        json_name = '{}_{}{}'.format(case['case'].replace(', ', '_').replace(' ', '_'), tool, core_config.CASE_REPORT_SUFFIX)
        with open(os.path.join(args.output, json_name), 'r') as f:
            report = json.load(f)

        report[0]['test_status'] = status
        with open(os.path.join(args.output, json_name), 'w') as f:
            json.dump(report, f, indent=4)

    outs = ' '.join(outs)
    errs = ' '.join(errs)

    with open('{}_{}.log'.format(case['case'].replace(', ', '_').replace(' ', '_'), tool), 'w', encoding='utf-8') as file:
        file.write(outs)
        file.write(errs)


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
        else:
            case['status'] = 'active'

        template = {}
        template['render_device'] = get_gpu()
        template['onnx'] = case['onnx']
        template['test_group'] = args.testType
        template['date_time'] = datetime.now().strftime(
            '%m/%d/%Y %H:%M:%S')
        if case['status'] == 'skipped':
            template['test_status'] = 'skipped'
        else:
            template['test_status'] = 'error'

        for tool in ['rml', 'winml', 'tensorrt']:
            template_copy = template.copy()
            if tool == 'rml':
                template_copy['bin'] = case['bin']
            else:
                template_copy['csv'] = case['csv']
            template_copy['case'] = '{}, {}'.format(case['case'], tool)
            case_name = template_copy['case'].replace(', ', '_').replace(' ', '_')
            with open(os.path.join(args.output, case_name + core_config.CASE_REPORT_SUFFIX), 'w') as f:
                f.write(json.dumps([template_copy], indent=4))

    args.rmlTool = os.path.abspath(args.rmlTool)

    for case in cases:
        if case['status'] != 'skipped':
            onnx_path = os.path.join(args.res_path, case['onnx']).replace('/', os.path.sep)
            csv_path = os.path.join(args.data_path, case['csv']).replace('/', os.path.sep)
            bin_path = os.path.join(args.data_path, case['bin']).replace('/', os.path.sep)
            case_name = case['case'].replace(', ', '_').replace(' ', '_')

            cmd_line = case['cmd_line_rml']
            cmd_script = cmd_line.format(tool_path=args.rmlTool, onnx_path=onnx_path, bin_path=bin_path)
            cmd_script_path = os.path.join(args.output, '{}_rml.bat'.format(case_name))
            execute_case(args, case, 'rml', cmd_script, cmd_script_path)

            cmd_line = case['cmd_line_winml']
            cmd_script = cmd_line.format(tool_path=args.winmlTool, onnx_path=onnx_path, csv_path=csv_path)
            cmd_script_path = os.path.join(args.output, '{}_winml.bat'.format(case_name))
            execute_case(args, case, 'winml', cmd_script, cmd_script_path)

            cmd_line = case['cmd_line_tensorrt']
            cmd_script = cmd_line.format(tool_path=args.tensorrtTool, onnx_path=onnx_path, csv_path=csv_path)
            cmd_script_path = os.path.join(args.output, '{}_tensorrt.bat'.format(case_name))
            execute_case(args, case, 'tensorrt', cmd_script, cmd_script_path)

    exit(0)
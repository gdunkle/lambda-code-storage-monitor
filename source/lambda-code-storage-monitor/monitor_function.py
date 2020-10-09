#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Amazon Software License (the "License"). You may not   #
#  use this file except in compliance with the License. A copy of the        #
#  License is located at                                                     #
#                                                                            #
#      http://aws.amazon.com/asl/                                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is distributed #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,        #
#  express or implied. See the License for the specific language governing   #
#  permissions and limitations under the License.                            #
##############################################################################

import logging
import json
import os
import traceback
import sys
import boto3
from botocore.config import Config

config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)
lambda_client = boto3.client("lambda", config=config)
cloud_watch_client = boto3.client("cloudwatch", config=config)
DEFAULT_PAGE_SIZE = int(os.environ.get('PAGE_SIZE'))


def lambda_handler(event, context):
    try:
        logging.debug(event)
        results = get_function_sizes()
        publish_total_size_metric(results)
        result = {
            'statusCode': '200',
            'results': results
        }
        return json.dumps(result)
    except Exception as error:
        logging.error('lambda_handler error: %s' % error)
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        result = {
            'statusCode': '500',
            'body': {'message': 'error'}
        }
        return json.dumps(result)


def publish_total_size_metric(results: dict):
    metricData = [
        {
            'MetricName': 'Code Size',
            'Dimensions': [
                {
                    'Name': 'Code Size',
                    'Value': 'All Functions'
                },
            ],
            'Value': results["Total"],

            'Unit': 'Bytes'

        },
    ]
    for name, sizes in results["Functions"].items():
        metricData.append({
            'MetricName': 'CodeSize',
            'Dimensions': [
                {
                    'Name': 'Code Size',
                    'Value': name
                },
            ],
            'Value': sizes["Total"],
            'Unit': 'Bytes'
        })
    cloud_watch_client.put_metric_data(
        Namespace='Custom/Lambda',
        MetricData=metricData
    )


def get_function_sizes(results: dict = {}) -> dict:
    marker = results["NextMarker"] if "NextMarker" in results.keys() else None
    results["Functions"] = functions = results["Functions"] if "Functions" in results.keys() else {}
    total = results["Total"] if "Total" in results.keys() else 0
    args = {"MaxItems": DEFAULT_PAGE_SIZE}
    if marker is not None:
        args["Marker"] = marker
    response = lambda_client.list_functions(**args)
    results["NextMarker"] = response['NextMarker'] if "NextMarker" in response.keys() else None
    for fn in response['Functions']:
        function_name = fn["FunctionName"]
        version_sizes = get_function_version_sizes(function_name)
        if version_sizes["Functions"] is not None:
            functions.update(version_sizes["Functions"])
        if version_sizes["Total"] is not None:
            total += version_sizes["Total"]
    results["Total"] = total
    if results["NextMarker"] is not None:
        results = get_function_sizes(results)
    return results


def get_function_version_sizes(function_name: str, results: dict = {}) -> dict:
    marker = results["NextMarker"] if "NextMarker" in results.keys() else None
    results["Functions"] = functions = results["Functions"] if "Functions" in results.keys() else {}
    total = results["Total"] if "Total" in results.keys() else 0
    args = {"MaxItems": DEFAULT_PAGE_SIZE, "FunctionName": function_name}
    if marker is not None:
        args["Marker"] = marker
    response = lambda_client.list_versions_by_function(**args)
    results["NextMarker"] = response['NextMarker'] if "NextMarker" in response.keys() else None
    for fn in response['Versions']:
        function_name = fn["FunctionName"]
        function_version = fn["Version"]
        function_size = fn["CodeSize"]
        logging.debug(f"{function_name}:{function_version} = {function_size}")
        functions[function_name] = versions = functions[function_name] if function_name in functions.keys() else {}
        versions[function_version] = function_size
        sub_total = versions["Total"] if "Total" in versions.keys() else 0
        sub_total += function_size
        versions["Total"] = sub_total
        total += function_size
    results["Total"] = total
    if results["NextMarker"] is not None:
        results = get_function_version_sizes(function_name, results)
    return results


def init_logger():
    global log_level
    log_level = str(os.environ.get('LOG_LEVEL')).upper()
    if log_level not in [
        'DEBUG', 'INFO',
        'WARNING', 'ERROR',
        'CRITICAL'
    ]:
        log_level = 'ERROR'
    logging.getLogger().setLevel(log_level)


init_logger()

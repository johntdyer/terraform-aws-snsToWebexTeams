#!/usr/bin/env python
#-*- coding: latin-1 -*-
#
# Copyright (c) 2017 Naoto Yokoyama
#
# Modifications applied to the original work.
#
#
# Original copyright notice:
#
# Copyright 2018 John Dyer
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
'''
Parse an SNS event message and send to a Spark space
'''
from __future__ import print_function

import os
import json
import base64
import re
import requests

from base64 import b64decode

__author__ = "John Dyer (@thedyers)"
__copyright__ = "Copyright 2018 John Dyer"
__credits__ = ["John Dyer"]
__license__ = "Apache License, 2.0"
__version__ = "0.1.2"
__maintainer__ = "John Dyer"
__email__ = "johntdyer@gmail.com"
__status__ = "Production"

DEFAULT_EVENT_TYPE = os.environ.get('DEFAULT_EVENT_TYPE', 'SNS Event')
DEFAULT_UNICODE_ICON = os.environ.get('DEFAULT_UNICODE_ICON', 'ℹ️')

DEFAULT_SPARK_ENDPOINT = os.environ.get('SPARK_API', 'api.ciscospark.com/v1/messages')

def get_spark_emoji(event_src, topic_name, event_cond='default'):
    '''Map an event source, severity, and condition to an unicode emoji
    '''
    # print("get_spark_emoji: <event_src: '{0}'| topic_name: '{1}' | event_cond: '{2}'>".format(event_src, topic_name,event_cond))
    emoji_map = {
        'autoscaling': {
            'notices': {'default': '⚖️'}},
        'cloudwatch': {
            'notices': {
                'ok': '✅',
                'alarm': '❗',
                'insuffcient_data': '❓'},
            'alerts': {
                'ok': '✅',
                'alarm': '❗',
                'insuffcient_data': '❓'}},
        'elasticache': {
            'notices': {'default': '⏱️'}},
        'rds': {
            'notices': {'default': '®️'}}}

    try:
        return emoji_map[event_src][topic_name.split('-')[1]][event_cond]
    except KeyError:
        if topic_name == 'alerts':
            return '🔥'
        else:
            return DEFAULT_UNICODE_ICON

def get_event_alias(event_src):
    '''Map event source to the more descriptive name
    '''
    event_alias_map = {
        'cloudwatch': 'AWS CloudWatch',
        'autoscaling': 'AWS AutoScaling',
        'elasticache': 'AWS ElastiCache',
        'rds': 'AWS RDS'}

    try:
        return event_alias_map[event_src]
    except KeyError:
        return DEFAULT_EVENT_TYPE


def get_spark_space(region, event_src, topic_name, channel_map):
    '''Map region and event type to Spark channel name
    '''
    try:
        return channel_map[topic_name]
    except KeyError:
        return DEFAULT_CHANNEL


def autoscaling_capacity_change(cause):
    '''
    '''
    s = re.search(r'capacity from (\w+ to \w+)', cause)
    if s:
        return s.group(0)


def lambda_handler(event, context):
    '''The Lambda function handler
    '''

    config = {
      'bearer_token': 'Bearer ' + os.environ['SPARK_TOKEN'],
      'webhook_url': 'api.ciscospark.com/v1/messages',
      'channel_map': json.loads(base64.b64decode(os.environ['CHANNEL_MAP']))
    }

    event_cond = 'default'
    sns = event['Records'][0]['Sns']
    print('DEBUG EVENT:', sns['Message'])
    json_msg = json.loads(sns['Message'])

    if sns['Subject']:
        message = sns['Subject']
    else:
        message = sns['Message']


    # SNS Topic ARN: arn:aws:sns:<REGION>:<AWS_ACCOUNT_ID>:<TOPIC_NAME>
    #
    # SNS Topic Names => Spark Channels
    #  <env>-alerts => alerts-<region>
    #  <env>-notices => events-<region>
    #
    region = sns['TopicArn'].split(':')[3]
    topic_name = sns['TopicArn'].split(':')[-1]
    spark_message = ""
    if json_msg.get('AlarmName'):
        event_src = 'cloudwatch'

        color_map = {
                'OK': 'primary',
                'INSUFFICIENT_DATA': 'warning',
                'ALARM': 'danger'
        }
        event_cond = json_msg['NewStateValue']

        dictionary =  {
            'color_class': color_map[event_cond],
            'alarm_name':  json_msg['AlarmName'],
            'alarm_description': json_msg['AlarmDescription'],
            'alarm_status': json_msg['NewStateValue'],
            'old_status': json_msg['OldStateValue'],
            'alarm_reason': json_msg['NewStateReason'],
            'namespace': json_msg['Trigger']['Namespace'],
            'metric_name': json_msg['Trigger']['MetricName'],
            'event_alias': get_event_alias(event_src),
            'event_icon': get_spark_emoji(event_src, topic_name, event_cond.lower())
        }

        spark_message = """<h2>{event_icon} {event_alias}</h2>
        <hr/>
        <blockquote class=\"{color_class}\">
        <li><b>Name:</b> {alarm_name}</li>
        <li><b>Description:</b> {alarm_description}</li>
        <li><b>Status:</b> {alarm_status}</li>
        <li><b>Trigger:</b> {alarm_reason}</li>
        <li><b>Transition:</b> '{old_status}' --> {alarm_status} </li>
        <li><b>Namespace:</b> {namespace} - {metric_name}</li>
        </blockquote>
        """

    elif json_msg.get('Cause'):
        event_src = 'autoscaling'

        dictionary =  {
            'color_class': 'primary',
            'alarm_name':  json_msg['Event'],
            'alarm_status': autoscaling_capacity_change(json_msg['Cause']),
            'alarm_reason': json_msg['Cause'],
            'event_alias': get_event_alias(event_src),
            'event_icon': get_spark_emoji(event_src, topic_name, event_cond.lower())
        }

        spark_message = """<h2>{event_icon} {event_alias}</h2>
        <hr/>
        <blockquote class=\"{color_class}\">
        <li><b>Name</b> {alarm_name}</li>
        <li><b>Status</b> {alarm_status}</li>
        <li><b>Reason</b> {alarm_reason}</li>
        </blockquote>
        """
    elif json_msg.get('ElastiCache:SnapshotComplete'):
        event_src = 'elasticache'

        dictionary =  {
            'color_class': 'primary',
            'alarm_name':  'ElastiCache Snapshot',
            'alarm_reason': 'Snapshot Complete',
            'event_alias': get_event_alias(event_src),
            'event_icon': get_spark_emoji(event_src, topic_name, event_cond.lower())
        }
        spark_message = """<h2>{event_icon} {event_alias}</h2>
        <hr/>
        <blockquote class=\"{color_class}\">
        <li><b>Name</b> {alarm_name}</li>
        <li><b>Status</b> {alarm_status}</li>
        <li><b>Reason</b> {alarm_reason}</li>
        </blockquote>
        """

    elif re.match("RDS", sns.get('Subject') or ''):
        event_src = 'rds'

        SourceId = json_msg['Identifier Link'].split("SourceId: ")[1]

        if json_msg.get('Identifier Link'):
            title_arr = json_msg['Identifier Link'].split('\n')
            if len(title_arr) >= 2:
                title_str = title_arr[1]
                title_lnk_str = title_arr[0]
            else:
                title_str = title_lnk_str = title_arr[0]
        dictionary =  {
            'color_class': 'primary',
            'alarm_name':  "{0} '{1}'".format(json_msg['Event Source'], title_str),
            'alarm_reason': json_msg['Event Message'],
            'alarm_status' : "N/A",
            'event_alias': get_event_alias(event_src),
            'event_icon': get_spark_emoji(event_src, topic_name, event_cond.lower())
        }
        spark_message = """<h2>{event_icon} {event_alias}</h2>
        <hr/>
        <blockquote class=\"{color_class}\">
        <li><b>Name</b> {alarm_name}</li>
        <li><b>Status</b> {alarm_status}</li>
        <li><b>Reason</b> {alarm_reason}</li>
        </blockquote>
        """
    else:
        event_src = 'other'

    event_env = topic_name.split('-')[0]
    event_sev = topic_name.split('-')[1]

    # print('DEBUG:', topic_name, region, event_env, event_sev, event_src)

    channel_map = config['channel_map']


    payload = {
        'markdown': spark_message.format(**dictionary).replace('\n', ' ').replace('\r', ''),
        'roomId' : get_spark_space(region, event_src, topic_name, channel_map),
    }
    # print('DEBUG PAYLOAD:', json.dumps(payload))
    headers = {'Authorization': config['bearer_token']}
    r = requests.post("https://" + config['webhook_url'], json=payload, headers=headers)
    return r.status_code

# Test locally
if __name__ == '__main__':

    sns_rds_event_template = json.loads(r"""
{
  "Records": [
    {
      "EventVersion": "1",
      "EventSubscriptionArn": "arn:aws:sns:us-east-1:852318511395:rds-automatic-snapshot-verification:f4a8e143-5576-4907-a3c4-8102a85122a0",
      "EventSource": "aws:sns",
      "Sns": {
        "Type" : "Delete",
        "MessageId" : "9230840c-8c9f-5f8d-b245-cb9feff6099a",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:production-notices",
        "Subject" : "RDS Notification Message",
        "Message" : "{\"Event Source\":\"db-instance\",\"Event Time\":\"2016-04-21 23:17:32.957\",\"Identifier Link\":\"https://console.aws.amazon.com/rds/home?region=us-west-2#\\nSourceId: wolftwo-hipchat \",\"Event ID\":\"http://docs.amazonwebservices.com/AmazonRDS/latest/UserGuide/USER_Events.html#RDS-EVENT-0003 \",\"Event Message\":\"The DB instance is being deleted.\"}",
        "Timestamp" : "2016-04-21T23:24:25.060Z",
        "SignatureVersion" : "1",
        "Signature" : "Od/I4sqXSrS6iTUXD8cWb5qXfa1+EnQgvDXvvzrmoljZw2L7li3H4aR1aa6Pfb4a/evdqKlfk5zbWTM0wqQrxr5tvFc141IYLper7bAxIGGL7F1+V/wCGpv0p2WwinNXGzvLr7Lq0gFVqxGC74ftDLCQ2XGFqLgRTGkLn2dnqLdUwJIzQ1X1n0AGIe+D4CokGkKZaaEOZvDFXVs9yF0kbXHg3aYRfkkUvYRH2jjogjnQwvGvjKCfe0aOQnZd2ZCVzxD+ctYSF7SMFQz+tD0hHNd8nIn7g/NC4LjjbPUSmMenaXcDjhQev1oHh05jAnWLtvcBMJhCF5bmPOqk0rdPXw==",
        "SigningCertURL" : "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-bb750dd426d95ee9390147a5624348ee.pem",
        "UnsubscribeURL" : "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:852318511395:rds-automatic-snapshot-verification-instances:61533c51-3260-45d5-9b2f-d8ac789ba5d0"
      }
    }
  ]
}""")


    sns_cloudwatch_ok_event_template = json.loads(r"""
{
  "Records": [
    {
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:EXAMPLE",
      "EventSource": "aws:sns",
      "Sns": {
        "SignatureVersion": "1",
        "Timestamp": "1970-01-01T00:00:00.000Z",
        "Signature": "EXAMPLE",
        "SigningCertUrl": "EXAMPLE",
        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
        "Message": "{\"AlarmName\":\"sns-spark-test-from-cloudwatch-total-cpu\",\"AlarmDescription\":null,\"AWSAccountId\":\"123456789012\",\"NewStateValue\":\"OK\",\"NewStateReason\":\"Threshold Crossed: 1 datapoint (7.9053535353535365) was not greater than or equal to the threshold (8.0).\",\"StateChangeTime\":\"2015-11-09T21:19:43.454+0000\",\"Region\":\"US - N. Virginia\",\"OldStateValue\":\"ALARM\",\"Trigger\":{\"MetricName\":\"CPUUtilization\",\"Namespace\":\"AWS/EC2\",\"Statistic\":\"AVERAGE\",\"Unit\":null,\"Dimensions\":[],\"Period\":300,\"EvaluationPeriods\":1,\"ComparisonOperator\":\"GreaterThanOrEqualToThreshold\",\"Threshold\":8.0}}",
        "MessageAttributes": {
          "Test": {
            "Type": "String",
            "Value": "TestString"
          },
          "TestBinary": {
            "Type": "Binary",
            "Value": "TestBinary"
          }
        },
        "Type": "Notification",
        "UnsubscribeUrl": "EXAMPLE",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:production-notices",
        "Subject": "OK: sns-spark-test-from-cloudwatch-total-cpu"
      }
    }
  ]
}""")


    sns_cloudwatch_alarm_event_template = json.loads(r"""
{
  "Records": [
    {
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:EXAMPLE",
      "EventSource": "aws:sns",
      "Sns": {
        "SignatureVersion": "1",
        "Timestamp": "1970-01-01T00:00:00.000Z",
        "Signature": "EXAMPLE",
        "SigningCertUrl": "EXAMPLE",
        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
        "Message": "{\"AlarmName\":\"sns-spark-test-from-cloudwatch-total-cpu\",\"AlarmDescription\":null,\"AWSAccountId\":\"123456789012\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Threshold Crossed: 1 datapoint (7.9053535353535365) was not greater than or equal to the threshold (8.0).\",\"StateChangeTime\":\"2015-11-09T21:19:43.454+0000\",\"Region\":\"US - N. Virginia\",\"OldStateValue\":\"ALARM\",\"Trigger\":{\"MetricName\":\"CPUUtilization\",\"Namespace\":\"AWS/EC2\",\"Statistic\":\"AVERAGE\",\"Unit\":null,\"Dimensions\":[],\"Period\":300,\"EvaluationPeriods\":1,\"ComparisonOperator\":\"GreaterThanOrEqualToThreshold\",\"Threshold\":8.0}}",
        "MessageAttributes": {
          "Test": {
            "Type": "String",
            "Value": "TestString"
          },
          "TestBinary": {
            "Type": "Binary",
            "Value": "TestBinary"
          }
        },
        "Type": "Notification",
        "UnsubscribeUrl": "EXAMPLE",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:production-notices",
        "Subject": "ALARM: sns-spark-test-from-cloudwatch-total-cpu"
      }
    }
  ]
}""")

    sns_cloudwatch_unknown_event_template = json.loads(r"""
{
  "Records": [
    {
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:EXAMPLE",
      "EventSource": "aws:sns",
      "Sns": {
        "SignatureVersion": "1",
        "Timestamp": "1970-01-01T00:00:00.000Z",
        "Signature": "EXAMPLE",
        "SigningCertUrl": "EXAMPLE",
        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
        "Message": "{\"AlarmName\":\"sns-spark-test-from-cloudwatch-total-cpu\",\"AlarmDescription\":null,\"AWSAccountId\":\"123456789012\",\"NewStateValue\":\"INSUFFICIENT_DATA\",\"NewStateReason\":\"Threshold Crossed: 1 datapoint (7.9053535353535365) was not greater than or equal to the threshold (8.0).\",\"StateChangeTime\":\"2015-11-09T21:19:43.454+0000\",\"Region\":\"US - N. Virginia\",\"OldStateValue\":\"ALARM\",\"Trigger\":{\"MetricName\":\"CPUUtilization\",\"Namespace\":\"AWS/EC2\",\"Statistic\":\"AVERAGE\",\"Unit\":null,\"Dimensions\":[],\"Period\":300,\"EvaluationPeriods\":1,\"ComparisonOperator\":\"GreaterThanOrEqualToThreshold\",\"Threshold\":8.0}}",
        "MessageAttributes": {
          "Test": {
            "Type": "String",
            "Value": "TestString"
          },
          "TestBinary": {
            "Type": "Binary",
            "Value": "TestBinary"
          }
        },
        "Type": "Notification",
        "UnsubscribeUrl": "EXAMPLE",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:production-notices",
        "Subject": "INSUFFICIENT_DATA: sns-spark-test-from-cloudwatch-total-cpu"
      }
    }
  ]
}""")

    sns_autoscale_event_template = json.loads(r"""
{

    "Records": [{
        "EventSource": "aws:sns",
        "EventVersion": "1.0",
        "EventSubscriptionArn": "arn:aws:sns:us-east-1:123456789123:AutoScalingNotifications:00000000-0000-0000-0000-000000000000",
        "Sns": {
            "Type": "Notification",
            "MessageId": "00000000-0000-0000-0000-000000000000",
            "TopicArn": "arn:aws:sns:us-east-1:123456789012:production-notices",
            "Subject": "Auto Scaling: termination for group \"autoscale-group-name\"",
            "Message": "{\"Progress\":50,\"AccountId\":\"123456789123\",\"Description\":\"Terminating EC2 instance: i-00000000\",\"RequestId\":\"00000000-0000-0000-0000-000000000000\",\"EndTime\":\"2016-09-16T12:39:01.604Z\",\"AutoScalingGroupARN\":\"arn:aws:autoscaling:us-east-1:123456789:autoScalingGroup:00000000-0000-0000-0000-000000000000:autoScalingGroupName/autoscale-group-name\",\"ActivityId\":\"00000000-0000-0000-0000-000000000000\",\"StartTime\":\"2016-09-16T12:37:39.004Z\",\"Service\":\"AWS Auto Scaling\",\"Time\":\"2016-09-16T12:39:01.604Z\",\"EC2InstanceId\":\"i-00000000\",\"StatusCode\":\"InProgress\",\"StatusMessage\":\"\",\"Details\":{\"Subnet ID\":\"subnet-00000000\",\"Availability Zone\":\"us-east-1a\"},\"AutoScalingGroupName\":\"autoscale-group-name\",\"Cause\":\"At 2016-09-16T12:37:09Z a user request update of AutoScalingGroup constraints to min: 0, max: 0, desired: 0 changing the desired capacity from 1 to 0.  At 2016-09-16T12:37:38Z an instance was taken out of service in response to a difference between desired and actual capacity, shrinking the capacity from 1 to 0.  At 2016-09-16T12:37:39Z instance i-00000000 was selected for termination.\",\"Event\":\"autoscaling:EC2_INSTANCE_TERMINATE\"}",
            "Timestamp": "2016-09-16T12:39:01.661Z",
            "MessageAttributes": {}
        }
    }]
}
""")


    print('running locally')
    print(lambda_handler(sns_autoscale_event_template, None))
    print(lambda_handler(sns_rds_event_template, None))
    print(lambda_handler(sns_cloudwatch_ok_event_template, None))
    print(lambda_handler(sns_cloudwatch_alarm_event_template, None))
    print(lambda_handler(sns_cloudwatch_unknown_event_template, None))

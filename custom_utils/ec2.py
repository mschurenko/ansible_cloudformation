#!/usr/bin/env python

# Stolen from: ansible/module_utils/ec2.py

import boto
import boto.ec2
import ConfigParser
import os
import sys
from boto.sts import STSConnection

def boto_supports_profile_name():
    return hasattr(boto.ec2.EC2Connection, 'profile_name')

def config_section_map(config, section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
        except:
            dict1[option] = None
    return dict1


def get_aws_connection_info(module):
    ec2_url = module.params.get('ec2_url')
    access_key = module.params.get('aws_access_key')
    secret_key = module.params.get('aws_secret_key')
    security_token = module.params.get('security_token')
    region = module.params.get('region')
    aws_profile = module.params.get('aws_profile')
    validate_certs = module.params.get('validate_certs')

    profile_dict = {}

    if not ec2_url:
        if 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']
        elif 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']

    if not region:
        if 'EC2_REGION' in os.environ:
            region = os.environ['EC2_REGION']
        elif 'AWS_REGION' in os.environ:
            region = os.environ['AWS_REGION']
        else:
            # boto.config.get returns None if config not found
            region = boto.config.get('Boto', 'aws_region')
            if not region:
                region = boto.config.get('Boto', 'ec2_region')

    if aws_profile:
        # sanity checks
        if aws_profile != "default":
            if "HOME" not in os.environ:
                module.fail_json(msg="No $HOME environment variable could be detected. Do you even UNIX bro?")

            aws_config_file = os.path.join(os.environ["HOME"], ".aws/config")
            if not os.path.exists(aws_config_file):
                module.fail_json(msg="Does $HOME/aws/.config even exist?")

            config = ConfigParser.ConfigParser()
            config.read(aws_config_file)

            sections = config.sections()

            if 'profile ' + aws_profile not in sections:
                module.fail_json(msg="AWS profile: %s was not found" % aws_profile)

            profile_dict = config_section_map(config, 'profile ' + aws_profile)
    else:
        aws_profile = None

    if profile_dict and 'role_arn' in profile_dict:
        role_arn = profile_dict['role_arn']
        source_profile = profile_dict['source_profile']
        role_session_name = 'CustomAnsibleSession'

        # get creds by following source_profile
        aws_credentials_file = os.path.join(os.environ["HOME"], ".aws/credentials")
        if not os.path.exists(aws_credentials_file):
            module.fail_json(msg="Does $HOME/aws/.credentials even exist?")

        config.read(aws_credentials_file)

        source_profile_dict = config_section_map(config, source_profile)

        aws_access_key = source_profile_dict['aws_access_key_id']
        aws_secret_key = source_profile_dict['aws_secret_access_key']

        sts_connection = STSConnection(aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)

        assumedRoleObject = sts_connection.assume_role(
            role_arn=role_arn,
            role_session_name=role_session_name
        )
        access_key = assumedRoleObject.credentials.access_key
        secret_key = assumedRoleObject.credentials.secret_key
        security_token = assumedRoleObject.credentials.session_token

    else:
        if not access_key:
            if 'EC2_ACCESS_KEY' in os.environ:
                access_key = os.environ['EC2_ACCESS_KEY']
            elif 'AWS_ACCESS_KEY_ID' in os.environ:
                access_key = os.environ['AWS_ACCESS_KEY_ID']
            elif 'AWS_ACCESS_KEY' in os.environ:
                access_key = os.environ['AWS_ACCESS_KEY']
            else:
                # in case access_key came in as empty string
                access_key = None

        if not secret_key:
            if 'EC2_SECRET_KEY' in os.environ:
                secret_key = os.environ['EC2_SECRET_KEY']
            elif 'AWS_SECRET_ACCESS_KEY' in os.environ:
                secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
            elif 'AWS_SECRET_KEY' in os.environ:
                secret_key = os.environ['AWS_SECRET_KEY']
            else:
                # in case secret_key came in as empty string
                secret_key = None

            if not security_token:
                if 'AWS_SECURITY_TOKEN' in os.environ:
                    security_token = os.environ['AWS_SECURITY_TOKEN']
            else:
                # in case security_token came in as empty string
                security_token = None

    boto_params = dict(aws_access_key_id=access_key,
                       aws_secret_access_key=secret_key,
                       profile_name=aws_profile,
                       security_token=security_token)

    return region, ec2_url, boto_params
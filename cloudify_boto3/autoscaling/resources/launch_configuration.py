# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
"""
    Autoscaling.LaunchConfiguration
    ~~~~~~~~~~~~~~
    AWS Autoscaling Launch Configuration interface
"""
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.autoscaling import AutoscalingBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'Autoscaling Launch Configuration'
LCS = 'LaunchConfigurations'
RESOURCE_NAMES = 'LaunchConfigurationNames'
RESOURCE_NAME = 'LaunchConfigurationName'
LC_ARN = 'LaunchConfigurationARN'
IMAGEID = 'ImageId'
INSTANCEID = 'InstanceId'
INSTANCE_TYPE = 'cloudify.aws.nodes.Instance'
INSTANCE_TYPE_PROPERTY = 'InstanceType'
INSTANCE_TYPE_PROPERTY_DEPRECATED = 'instance_type'
SECGROUPS = 'SecurityGroups'
SECGROUP_TYPE = 'cloudify.aws.nodes.SecurityGroup'


class AutoscalingLaunchConfiguration(AutoscalingBase):
    """
        Autoscaling Autoscaling Launch Configuration interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        AutoscalingBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        params = {RESOURCE_NAMES: [self.resource_id]}
        try:
            resources = \
                self.client.describe_launch_configurations(**params)
        except ClientError:
            pass
        else:
            return resources.get(LCS, [None])[0]

    @property
    def status(self):
        """Gets the status of an external resource"""
        props = self.properties
        if not props:
            return None
        return None

    def create(self, params):
        """
            Create a new AWS Autoscaling Autoscaling Launch Configuration.
        """
        if not self.resource_id:
            setattr(self, 'resource_id', params.get(RESOURCE_NAME))
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_launch_configuration(**params)
        launch_configuration = self.properties
        self.logger.debug('Response: %s' % res)
        return launch_configuration.get(LC_ARN)

    def delete(self, params=None):
        """
            Deletes an existing AWS Autoscaling Autoscaling
            Launch Configuration.
        """
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_launch_configuration(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS Autoscaling Autoscaling Launch Configuration"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(AutoscalingLaunchConfiguration, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    """Creates an AWS Autoscaling Autoscaling Launch Configuration"""
    params = \
        dict() if not resource_config else resource_config.copy()
    resource_id = \
        iface.resource_id or \
        utils.get_resource_id(
            ctx.node,
            ctx.instance,
            params.get(RESOURCE_NAME),
            use_instance_id=True)
    params[RESOURCE_NAME] = resource_id
    utils.update_resource_id(ctx.instance, resource_id)

    # Add Security Groups
    secgroups_list = params.get(SECGROUPS, [])
    params[SECGROUPS] = \
        utils.add_resources_from_rels(
            ctx.instance,
            SECGROUP_TYPE,
            secgroups_list)

    image_id = params.get(IMAGEID)

    # Add Instance and Instance Type
    instance_id = params.get(INSTANCEID)
    instance_type = params.get(INSTANCE_TYPE_PROPERTY)
    if not image_id and not instance_id:
        instance_id = utils.find_resource_id_by_type(
            ctx.instance,
            INSTANCE_TYPE)
        params.update({INSTANCEID: instance_id})
    if instance_id and not instance_type:
        targ = utils.find_rel_by_node_type(
            ctx.instance,
            INSTANCE_TYPE)
        if targ:
            instance_type = \
                targ.target.node.properties.get(
                    INSTANCE_TYPE_PROPERTY_DEPRECATED)
        params.update({INSTANCE_TYPE_PROPERTY: instance_type})

    utils.update_resource_id(
        ctx.instance, params.get(RESOURCE_NAME))
    iface.update_resource_id(params.get(RESOURCE_NAME))
    # Actually create the resource
    resource_arn = iface.create(params)
    utils.update_resource_arn(
        ctx.instance, resource_arn)


@decorators.aws_resource(AutoscalingLaunchConfiguration, RESOURCE_TYPE,
                         ignore_properties=True)
def delete(iface, resource_config, **_):
    """Deletes an AWS Autoscaling Autoscaling Launch Configuration"""
    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    if RESOURCE_NAME not in params.keys():
        params.update({RESOURCE_NAME: iface.resource_id})
    iface.delete(params)

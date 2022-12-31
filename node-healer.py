import os
import configparser
import requests
import boto3
import time

# Get the directory containing the script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Read variables from INI file
config = configparser.ConfigParser()
config.read(os.path.join(script_dir, 'config.ini'))

api_url = config.get('OpenShift', 'api_url')
api_token = config.get('OpenShift', 'api_token')
aws_access_key_id = config.get('AWS', 'access_key_id')
aws_secret_access_key = config.get('AWS', 'secret_access_key')
aws_region = config.get('AWS', 'region')
check_interval = config.getint('Options', 'check_interval')
teams_webhook_url = config.get('Teams', 'webhook_url')

# Set up AWS client
ec2 = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region)

def check_node_status(node_name):
  # Make a GET request to the OpenShift API to get the node's status
  headers = {'Authorization': f'Bearer {api_token}'}
  r = requests.get(f'{api_url}/api/v1/nodes/{node_name}', headers=headers, verify=False)
  r.raise_for_status()

  # Parse the response and return the node's status
  node_info = r.json()
  return node_info['status']['conditions'][0]['status']

def reboot_node(node_name):
  # Get the AWS instance ID of the node
  headers = {'Authorization': f'Bearer {api_token}'}
  r = requests.get(f'{api_url}/api/v1/nodes/{node_name}', headers=headers, verify=False)
  r.raise_for_status()
  node_info = r.json()
  instance_id = node_info['metadata']['labels']['beta.kubernetes.io/instance-id']

  # Reboot the instance using the AWS API
  ec2.reboot_instances(InstanceIds=[instance_id])

  # Post a message to the Microsoft Teams channel using the webhook
  message = {'text': f'Node {node_name} ({instance_id}) has been rebooted.'}
  requests.post(teams_webhook_url, json=message)

# Loop indefinitely
while True:
  # Make a GET request to the OpenShift API to get a list of all nodes
  headers = {'Authorization': f'Bearer {api_token}'}
  r = requests.get(f'{api_url}/api/v1/nodes', headers=headers, verify=False)
  r.raise_for_status()

  # Parse the response and get the names of all nodes
  nodes = r.json()
  node_names = [node['metadata']['name'] for node in nodes['items']]

  # Check the status of each node
  for node_name in node_names:
    status = check_node_status(node_name)
    if status != 'Ready':
      # Keep track of the number of consecutive checks that have returned a notready status
      if not hasattr(check_node_status, 'notready_count'):
        check_node_status.notready_count = 0
      check_node_status.notready_count += 1

      if check_node_status.notready_count >= 3:
        # Reboot the node if it has reported a notready status for 3 consecutive checks
        reboot_node(node_name)
    else:
      # Reset the notready count if the node is ready
      check_node_status.notready_count = 0

  # Sleep for the specified interval before checking the nodes again
  time.sleep(check_interval)

import boto3

def lambda_handler(event, context):
    
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')

    # SNS Topic ARN
    sns_topic_arn = 'arn:aws:sns:REGION:ACCOUNT_ID:YOUR_TOPIC_NAME' ### <--- Update Your SNS Topic ARN Here ###


    # Get all active volumes in our account
    volumes_response = ec2.describe_volumes()
    
    # Store active volumes in a list
    active_volume_ids = [vol['VolumeId'] for vol in volumes_response['Volumes']]


    # Get all PRIVATE snapshots with the help of --> "OwnerIds=['self']"
    snapshots_response = ec2.describe_snapshots(OwnerIds=['self'])  

    # Creating an empty list
    deleted_snapshots = []


    # Looping through every single snapshot 
    for snap in snapshots_response['Snapshots']:
        snapshot_id = snap['SnapshotId']
        
        # Get VolumeID of snapshots

        volume_id = snap.get('VolumeId') 

        if not volume_id:
            continue

        # If the snapshot's original volume ID is NOT found it is an orphan.
        if volume_id not in active_volume_ids:
            
            try:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                deleted_snapshots.append(snapshot_id) # Add it to our deleted list
                print(f"Successfully deleted orphaned snapshot: {snapshot_id}")
            except Exception as e:
                print(f"Skipping snapshot {snapshot_id}. Error: {str(e)}")

    #------- Sending An SNS Notification -------#

    if deleted_snapshots:
        message = f"Cost Optimization Alert: Automatically deleted the following orphaned EBS snapshots: \n{deleted_snapshots}"
        
        #Publish the message to the SNS topic
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject='Automated EBS Snapshot Cleanup Report',
            Message=message
        )
        print("SNS notification sent.")
    else:
        print("No orphaned snapshots found. No email sent.")

    #Successful return statement for Lambda
    return {
        'statusCode': 200,
        'body': 'Snapshot cleanup executed successfully.'
    }

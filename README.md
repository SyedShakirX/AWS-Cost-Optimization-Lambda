# AWS Cost Optimization: Automated EBS Snapshot Cleanup

##  Overview
In dynamic cloud environments, EBS snapshots are frequently created for backups. However, when the original EC2 instances and attached EBS volumes are terminated, these snapshots are often forgotten, leading to accumulating "orphan" storage costs. 

This project is a serverless, event-driven architecture designed to automatically identify and delete orphaned Amazon EBS snapshots, optimizing AWS storage costs. The function is executed on a weekly schedule and sends an automated email report to administrators via Amazon SNS if any deletions occur.

##  Architecture
1. **Amazon EventBridge (CloudWatch Events):** Triggers the Lambda function weekly via a Cron expression.
2. **AWS Lambda:** Executes the Python (Boto3) core logic.
3. **Amazon EC2/EBS:** The environment being scanned for active volumes and stale snapshots.
4. **Amazon SNS:** Dispatches an email notification alerting the admin of the exact snapshot IDs that were deleted.
5. **Amazon CloudWatch Logs:** Captures the execution history for monitoring and debugging.

##  Security & IAM (Principle of Least Privilege)
To ensure strict security and prevent accidental infrastructure damage, the Lambda execution role is bound by a custom inline JSON policy. Broad managed policies like `AmazonEC2FullAccess` were intentionally avoided.

The function operates entirely on the following minimal permissions:
* `ec2:DescribeVolumes`
* `ec2:DescribeSnapshots`
* `ec2:DeleteSnapshot`
* `sns:Publish`
* `logs:CreateLogGroup` / `logs:CreateLogStream` / `logs:PutLogEvents`

##  Core Logic Flow
1. **Fetch Active State:** The script first makes an API call to AWS to fetch a list of all currently active EBS `VolumeId`s in the account.
2. **Fetch Snapshots:** It then fetches all private snapshots owned by the account (`OwnerIds=['self']`).
3. **Filter:** It iterates through the snapshots. If a snapshot's underlying `VolumeId` is **not** found in the active volumes list, it is flagged as an orphan.
4. **Action:** The script safely deletes the orphaned snapshot using a `try/except` block to prevent crashes if a snapshot is locked.
5. **Notification:** If deletions occur, the deleted IDs are compiled into a message and published to an SNS topic.

##  Deployment Instructions
1. Create a Standard **SNS Topic** and subscribe your email address to it. Confirm the subscription in your inbox.
2. Create an **AWS Lambda** function using the Python 3.x runtime.
3. Attach the custom IAM execution role containing the permissions listed above.
4. Copy the Python code from `lambda_function.py` into the console.
5. Update the `sns_topic_arn` variable on Line 8 with your actual SNS Topic ARN.
6. Navigate to **Amazon EventBridge**, create a new Rule, select "Schedule", and input your desired cron expression (e.g., `cron(0 10 ? * SUN *)` for every Sunday at 10 AM). Set the target to your Lambda function.

## 📝 Example Output (CloudWatch Logs)
You can view a simulated execution history in the `execution-history.log` file included in this repository, demonstrating both a clean run (no orphans) and a successful deletion run.

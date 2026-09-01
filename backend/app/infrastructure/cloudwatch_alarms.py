"""
CloudWatch Alarm Configuration

This module defines CloudWatch alarm configurations for the Ayurveda AI Platform.
These alarms monitor critical metrics and trigger notifications when thresholds are breached.

AWS Code-Only Mode: This code defines alarm configurations but does not create
CloudWatch alarms. The actual alarms must be created manually after Sprint 8.
"""

import boto3
from typing import Dict, List
from app.core.config import settings


class CloudWatchAlarmManager:
    """Manager for CloudWatch alarm configuration."""

    def __init__(self):
        """Initialize CloudWatch client."""
        self.cloudwatch = boto3.client(
            'cloudwatch',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID if hasattr(settings, 'AWS_ACCESS_KEY_ID') else None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') else None,
        )
        self.sns = boto3.client(
            'sns',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID if hasattr(settings, 'AWS_ACCESS_KEY_ID') else None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') else None,
        )

    def get_alarm_definitions(self) -> List[Dict]:
        """
        Get all alarm definitions for the Ayurveda AI Platform.

        Returns:
            List of alarm configuration dictionaries
        """
        alarms = [
            # FastAPI 5xx Error Rate Alarm
            {
                "alarm_name": "ayurveda-ai-fastapi-5xx-error-rate",
                "alarm_description": "Alert when FastAPI 5xx error rate exceeds 5%",
                "metric_name": "5XXError",
                "namespace": "AWS/ApplicationELB",
                "statistic": "Sum",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 5,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "LoadBalancer", "Value": "ayurveda-ai-alb"}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # FastAPI Response Time Alarm
            {
                "alarm_name": "ayurveda-ai-fastapi-response-time",
                "alarm_description": "Alert when FastAPI response time exceeds 2 seconds",
                "metric_name": "TargetResponseTime",
                "namespace": "AWS/ApplicationELB",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 3,
                "threshold": 2.0,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "LoadBalancer", "Value": "ayurveda-ai-alb"}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # SQS Document Queue Depth Alarm
            {
                "alarm_name": "ayurveda-ai-sqs-document-queue-depth",
                "alarm_description": "Alert when document processing queue depth exceeds 1000",
                "metric_name": "ApproximateNumberOfMessagesVisible",
                "namespace": "AWS/SQS",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 1000,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "QueueName", "Value": settings.SQS_DOCUMENT_QUEUE_URL.split("/")[-1]}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # SQS Email Queue Depth Alarm
            {
                "alarm_name": "ayurveda-ai-sqs-email-queue-depth",
                "alarm_description": "Alert when email queue depth exceeds 500",
                "metric_name": "ApproximateNumberOfMessagesVisible",
                "namespace": "AWS/SQS",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 500,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "QueueName", "Value": settings.SQS_EMAIL_QUEUE_URL.split("/")[-1]}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # Bedrock Error Rate Alarm
            {
                "alarm_name": "ayurveda-ai-bedrock-error-rate",
                "alarm_description": "Alert when Bedrock invocation error rate exceeds 10%",
                "metric_name": "InvocationErrors",
                "namespace": "AWS/Bedrock",
                "statistic": "Sum",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 10,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "ModelId", "Value": settings.BEDROCK_MODEL_ID}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # Bedrock Latency Alarm
            {
                "alarm_name": "ayurveda-ai-bedrock-latency",
                "alarm_description": "Alert when Bedrock invocation latency exceeds 10 seconds",
                "metric_name": "InvocationLatency",
                "namespace": "AWS/Bedrock",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 3,
                "threshold": 10000,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "ModelId", "Value": settings.BEDROCK_MODEL_ID}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # Database Connection Pool Exhaustion Alarm
            {
                "alarm_name": "ayurveda-ai-db-connection-pool",
                "alarm_description": "Alert when database connection pool usage exceeds 80%",
                "metric_name": "DatabaseConnections",
                "namespace": "AWS/RDS",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 80,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "DBInstanceIdentifier", "Value": "ayurveda-ai-neon"}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # S3 4xx Error Rate Alarm
            {
                "alarm_name": "ayurveda-ai-s3-4xx-error-rate",
                "alarm_description": "Alert when S3 4xx error rate exceeds 5%",
                "metric_name": "4xxErrors",
                "namespace": "AWS/S3",
                "statistic": "Sum",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 5,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "BucketName", "Value": settings.S3_BUCKET_NAME}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # S3 5xx Error Rate Alarm
            {
                "alarm_name": "ayurveda-ai-s3-5xx-error-rate",
                "alarm_description": "Alert when S3 5xx error rate exceeds 1%",
                "metric_name": "5xxErrors",
                "namespace": "AWS/S3",
                "statistic": "Sum",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 1,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "BucketName", "Value": settings.S3_BUCKET_NAME}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # Cognito Authentication Failure Alarm
            {
                "alarm_name": "ayurveda-ai-cognito-auth-failures",
                "alarm_description": "Alert when Cognito authentication failures exceed 50 in 5 minutes",
                "metric_name": "SignInSuccess",
                "namespace": "AWS/Cognito",
                "statistic": "Sum",
                "period": 300,
                "evaluation_periods": 1,
                "threshold": 50,
                "comparison_operator": "LessThanThreshold",
                "dimensions": [
                    {"Name": "UserPool", "Value": settings.COGNITO_USER_POOL_ID}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # SES Bounce Rate Alarm
            {
                "alarm_name": "ayurveda-ai-ses-bounce-rate",
                "alarm_description": "Alert when SES bounce rate exceeds 5%",
                "metric_name": "Bounce",
                "namespace": "AWS/SES",
                "statistic": "Sum",
                "period": 300,
                "evaluation_periods": 2,
                "threshold": 5,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # Lightsail CPU Utilization Alarm
            {
                "alarm_name": "ayurveda-ai-lightsail-cpu",
                "alarm_description": "Alert when Lightsail CPU utilization exceeds 80%",
                "metric_name": "CPUUtilization",
                "namespace": "AWS/Lightsail",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 3,
                "threshold": 80,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "InstanceName", "Value": "ayurveda-ai-backend"}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },

            # Lightsail Memory Utilization Alarm
            {
                "alarm_name": "ayurveda-ai-lightsail-memory",
                "alarm_description": "Alert when Lightsail memory utilization exceeds 85%",
                "metric_name": "MemoryUtilization",
                "namespace": "AWS/Lightsail",
                "statistic": "Average",
                "period": 300,
                "evaluation_periods": 3,
                "threshold": 85,
                "comparison_operator": "GreaterThanThreshold",
                "dimensions": [
                    {"Name": "InstanceName", "Value": "ayurveda-ai-backend"}
                ],
                "treat_missing_data": "notBreaching",
                "alarm_actions": [self.get_sns_topic_arn("alerts")],
            },
        ]

        return alarms

    def get_sns_topic_arn(self, topic_name: str) -> str:
        """
        Get SNS topic ARN for alarm notifications.

        Args:
            topic_name: Name of the SNS topic

        Returns:
            SNS topic ARN
        """
        # This would be the actual SNS topic ARN
        # For now, return a placeholder
        return f"arn:aws:sns:{settings.AWS_REGION}:123456789012:ayurveda-ai-{topic_name}"

    def create_alarm(self, alarm_config: Dict) -> Dict:
        """
        Create a CloudWatch alarm.

        Args:
            alarm_config: Alarm configuration dictionary

        Returns:
            Response from CloudWatch API

        Raises:
            Exception: If alarm creation fails
        """
        try:
            response = self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_config["alarm_name"],
                AlarmDescription=alarm_config["alarm_description"],
                MetricName=alarm_config["metric_name"],
                Namespace=alarm_config["namespace"],
                Statistic=alarm_config["statistic"],
                Period=alarm_config["period"],
                EvaluationPeriods=alarm_config["evaluation_periods"],
                Threshold=alarm_config["threshold"],
                ComparisonOperator=alarm_config["comparison_operator"],
                Dimensions=alarm_config.get("dimensions", []),
                TreatMissingData=alarm_config.get("treat_missing_data", "missing"),
                AlarmActions=alarm_config.get("alarm_actions", []),
                OKActions=alarm_config.get("ok_actions", []),
                InsufficientDataActions=alarm_config.get("insufficient_data_actions", []),
            )
            return response

        except Exception as e:
            raise Exception(f"Failed to create CloudWatch alarm: {str(e)}")

    def create_all_alarms(self) -> List[Dict]:
        """
        Create all defined CloudWatch alarms.

        Returns:
            List of responses from CloudWatch API

        Raises:
            Exception: If any alarm creation fails
        """
        alarms = self.get_alarm_definitions()
        responses = []

        for alarm_config in alarms:
            try:
                response = self.create_alarm(alarm_config)
                responses.append({
                    "alarm_name": alarm_config["alarm_name"],
                    "status": "created",
                    "response": response,
                })
            except Exception as e:
                responses.append({
                    "alarm_name": alarm_config["alarm_name"],
                    "status": "failed",
                    "error": str(e),
                })

        return responses

    def delete_alarm(self, alarm_name: str) -> Dict:
        """
        Delete a CloudWatch alarm.

        Args:
            alarm_name: Name of the alarm to delete

        Returns:
            Response from CloudWatch API

        Raises:
            Exception: If alarm deletion fails
        """
        try:
            response = self.cloudwatch.delete_alarms(AlarmNames=[alarm_name])
            return response

        except Exception as e:
            raise Exception(f"Failed to delete CloudWatch alarm: {str(e)}")


# Create singleton instance
cloudwatch_alarm_manager = CloudWatchAlarmManager()

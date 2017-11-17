# -*- coding: utf-8 -*-

import boto3

sqs_resource = boto3.resource('sqs')


class SQSQueue:

    def __init__(self, aws_queue):
        self._aws_queue = aws_queue

    def __str__(self):
        return '<{}: {}>'.format(type(self).__name__, self.name)

    #
    # Classmethods
    #

    @classmethod
    def list_queues(cls, prefix=None):
        if prefix:
            options = {'QueueNamePrefix': prefix}
        else:
            options = {}
        queues = sqs_resource.queues.filter(**options)
        return [cls(q) for q in queues]

    @classmethod
    def get(cls, name_or_url):
        if name_or_url.startswith('http'):
            queue = sqs_resource.Queue(name_or_url)
        else:
            queue = sqs_resource.get_queue_by_name(QueueName=name_or_url)

        return cls(queue)

    #
    # Properties
    #

    @property
    def url(self):
        return self._aws_queue.url

    @property
    def name(self):
        return self.url.split('/')[-1]

    @property
    def count(self):
        count = self._aws_queue.attributes.get('ApproximateNumberOfMessages')
        if count:
            return int(count)
        return 0

    #
    # Public
    #

    def get_messages(self, limit=None):
        limit = limit or self.count
        max_receive = 10 if limit >= 10 else 1
        received = 0
        failed_retrieve = 0
        while received < limit:
            retrieved = self._aws_queue.receive_messages(
                MaxNumberOfMessages=max_receive,
            )
            if retrieved:
                failed_retrieve = 0
            else:
                failed_retrieve += 1

            for message in retrieved:
                if received <= limit:
                    received += 1
                    yield message
                else:
                    break

            if failed_retrieve >= 3:
                break

            remaining = limit - received
            max_receive = remaining if remaining < 10 else max_receive

    def delete_messages(self, limit=None, receipts=None):
        receipts = receipts or []
        message_ids = [r.split('#')[0] for r in receipts]
        count = 0
        if message_ids or limit:
            for message in self.get_messages(limit=limit):
                if receipts and message.message_id not in message_ids:
                    continue

                message.delete()
                count += 1
        else:
            return -1

        return count

    def send_message(self, content):
        response = self._aws_queue.send_message(MessageBody=content)
        return response['ResponseMetadata']['HTTPStatusCode'] == 200

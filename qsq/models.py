import re


class SQSQueue:

    def __init__(self, aws_queue):
        self._aws_queue = aws_queue

    def __str__(self):
        return '<{}: {}>'.format(type(self).__name__, self.name)

    #
    # Classmethods
    #

    @classmethod
    def list_queues(cls, resource, prefix=None, min_count=None, pattern=None):
        if prefix:
            options = {'QueueNamePrefix': prefix}
        else:
            options = {}

        queues = [cls(q) for q in resource.queues.filter(**options)]
        min_count = max(min_count or 0, 0)
        if min_count > 0:
            queues = [q for q in queues if q.count >= min_count]

        if pattern:
            searcher = re.compile(pattern)
            queues = [q for q in queues if searcher.search(q.name)]

        return queues

    @classmethod
    def get(cls, resource, name_or_url):
        if name_or_url.startswith('http'):
            queue = resource.Queue(name_or_url)
        else:
            queue = resource.get_queue_by_name(QueueName=name_or_url)

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
        return max(count and int(count) or 0, 0)

    #
    # Public
    #

    def get_messages(self, limit=None, delete=False):
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

                if delete:
                    message.delete()

            if failed_retrieve >= 3:
                break

            remaining = limit - received
            max_receive = remaining if remaining < 10 else max_receive

    def purge(self):
        return self._aws_queue.purge()

    def send_message(self, content):
        response = self._aws_queue.send_message(MessageBody=content)
        return response['ResponseMetadata']['HTTPStatusCode'] == 200

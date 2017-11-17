from unittest import mock

import pytest

from qsq.models import SQSQueue


@pytest.fixture
def queue_url():
    return 'https://queue.amazonaws.com/id/queue_name'


def test_list_queues():
    ft = mock.Mock(return_value=[])
    resource = mock.Mock(queues=mock.Mock(filter=ft))
    queues = SQSQueue.list_queues(resource)
    assert queues == []
    ft.assert_called_once_with()


def test_list_queues_with_prefix():
    ft = mock.Mock(return_value=[])
    resource = mock.Mock(queues=mock.Mock(filter=ft))
    queues = SQSQueue.list_queues(resource, prefix='test')
    assert queues == []
    ft.assert_called_once_with(QueueNamePrefix='test')


def test_list_queues_with_min_count():
    ft = mock.Mock(return_value=[
        mock.Mock(attributes={'ApproximateNumberOfMessages': 0}),
        mock.Mock(attributes={'ApproximateNumberOfMessages': 10}),
    ])
    resource = mock.Mock(queues=mock.Mock(filter=ft))
    queues = SQSQueue.list_queues(resource, min_count=1)
    assert len(queues) == 1
    assert queues[0].count == 10


def test_list_queues_with_pattern_match(queue_url):
    ft = mock.Mock(return_value=[
        mock.Mock(url=queue_url),
        mock.Mock(url=queue_url.replace('queue_name', 'foobar')),
    ])
    resource = mock.Mock(queues=mock.Mock(filter=ft))
    queues = SQSQueue.list_queues(resource, pattern='foobar')
    assert len(queues) == 1
    assert queues[0].name == 'foobar'


def test_queue_get_by_url(queue_url):
    resource = mock.Mock()
    queue = SQSQueue.get(resource, queue_url)
    resource.Queue.assert_called_once_with(queue_url)
    assert isinstance(queue, SQSQueue)


def test_queue_get_by_name(queue_url):
    resource = mock.Mock()
    name = queue_url.split('/')[-1]
    queue = SQSQueue.get(resource, name)
    resource.get_queue_by_name.assert_called_once_with(QueueName=name)
    assert isinstance(queue, SQSQueue)


def test_queue_url(queue_url):
    aws_queue = mock.Mock(url=queue_url)
    queue = SQSQueue(aws_queue)
    assert queue.url == aws_queue.url


def test_queue_name():
    aws_queue = mock.Mock(url='https://queue.amazonaws.com/id/queue_name')
    queue = SQSQueue(aws_queue)
    assert queue.name == 'queue_name'


@pytest.mark.parametrize('msg_count', [None, 0, 1, 1000])
def test_message_count(msg_count):
    aws_queue = mock.Mock(attributes={'ApproximateNumberOfMessages': msg_count})
    queue = SQSQueue(aws_queue)
    assert queue.count >= 0


def test_get_messages():
    aws_queue = mock.Mock(
        receive_messages=mock.Mock(return_value=['whatever']),
        attributes={'ApproximateNumberOfMessages': 1},
    )
    queue = SQSQueue(aws_queue)
    messages = list(queue.get_messages())
    assert len(messages) == 1
    assert aws_queue.receive_messages.call_count == 1
    aws_queue.receive_messages.assert_called_with(MaxNumberOfMessages=1)


def test_purge():
    aws_queue = mock.Mock(purge=mock.Mock())
    queue = SQSQueue(aws_queue)
    queue.purge()
    aws_queue.purge.assert_called_once_with()


def test_send_message_message():
    aws_queue = mock.Mock(
        send_message=mock.Mock(
            return_value={'ResponseMetadata': {'HTTPStatusCode': 200}}
        )
    )
    queue = SQSQueue(aws_queue)
    response = queue.send_message('foobar')
    aws_queue.send_message.assert_called_once_with(MessageBody='foobar')
    assert response is True

import json
import boto3

import click
# FIXME:
from click._compat import _default_text_stderr

from .exceptions import FilterError
from .filters import json_filter
from .models import SQSQueue


def get_resource(**options):
    return boto3.resource('sqs', **options)


@click.group()
def cli():
    """
    A CLI utility to help manage SQS queues and messages

    Configuration is taken from `~/.aws/credentials` or the following
    environment variables:

        - AWS_DEFAULT_REGION\n
        - AWS_ACCESS_KEY_ID\n
        - AWS_SECRET_ACCESS_KEY\n

    Further details at: http://docs.aws.amazon.com/pt_br/cli/latest/userguide/cli-chap-getting-started.html

    Whenever necessary, queues can be referenced using their name or URL.
    """
    pass


@cli.command('filter')
@click.argument('expression', required=True)
@click.argument('stream', type=click.File('r'), required=False)
@click.option('--indent', '-i', 'indent', default=2, type=int,
              help='JSON identation')
def apply_filter(expression, stream, indent):
    """
    Filter json stream using jmespath

    `expression` is a jmespath query string

    `stream` a text stream or file (default to stdin)
    """
    if not stream:
        stream = click.get_text_stream('stdin')

    with stream:
        try:
            data = json.load(stream)
        except json.decoder.JSONDecodeError:
            click.echo('read data are not a json, :-(', err=True)
            return

    try:
        results = json_filter(expression, data)
    except FilterError as exc:
        click.echo('{}'.format(exc), err=True)
        return

    click.echo('{}'.format(json.dumps(results, indent=indent)))
    return results or []


@cli.command('queues')
@click.option('--prefix', '-p', default=None,
              help='Display only queues starting with prefix')
@click.option('--match', '-m', default=None,
              help='Display only queues that matches regex')
@click.option('--min-count', '-c', 'min_count', default=None, type=int,
              help='Display only queues with a minimal message count')
@click.option('--indent', '-i', 'indent', default=2, type=int,
              help='JSON identation')
def list_queues(prefix, match, min_count, indent):
    """
    List and filter queues
    """
    results = {'queues': []}
    queues = SQSQueue.list_queues(get_resource(), prefix=prefix, min_count=min_count, pattern=match)
    label = 'Processing queues'
    with click.progressbar(queues, label=label, file=_default_text_stderr()) as queuebar:
        for queue in queuebar:
            results['queues'].append({
                'queue_url': queue.url,
                'queue_name': queue.name,
                'message_count': queue.count,
            })

    if results:
        click.echo(json.dumps(results, indent=indent))
    return results


@cli.command('msg-dump')
@click.argument('queue', required=True)
@click.option('--limit', '-l', 'msglimit', default=None, type=int,
              help='Limit the number of messages')
@click.option('--indent', '-i', 'indent', default=2, type=int,
              help='JSON identation')
@click.option('--delete', '-d', default=False, is_flag=True,
              help='Delete retrieved messages')
@click.option('--quiet', '-q', default=False, is_flag=True,
              help='Quiet mode (suppress any output or prompt)')
def dump_messages(queue, msglimit, indent, delete, quiet):
    """
    Retrieve messages from queue
    """
    queue = SQSQueue.get(get_resource(), queue)
    messages = queue.get_messages(limit=msglimit)
    results = {'messages': []}
    label = 'Processing messages'
    with click.progressbar(messages, label=label, file=_default_text_stderr()) as msgbar:
        for message in msgbar:
            try:
                message_data = json.loads(message.body)
                if message_data.get('Message'):
                    message_data['Message'] = json.loads(message_data['Message'])

                results['messages'].append({
                    'message': message_data,
                    'receipt': message.receipt_handle
                })
            except json.decoder.JSONDecodeError:
                click.echo('messages are not json, :-(', err=True)
                return

    if not quiet and results['messages']:
        click.echo(json.dumps(results, indent=indent))
    return results


@cli.command('msg-purge')
@click.argument('queue', required=True)
@click.option('--quiet', '-q', default=False, is_flag=True,
              help='Quiet mode (suppress any output or prompt)')
def remove_messages(queue, quiet):
    """
    Purge messages from queue
    """
    queue = SQSQueue.get(get_resource(), queue)
    confirmation = False
    if not quiet:
        confirmation = click.confirm(
            'This operation will remove all the messages.\nAre you sure about this ?',
            abort=True,
        )

    if confirmation:
        queue.purge()
        if not quiet:
            click.echo('"{}" purged'.format(queue.name))


@cli.command('msg-move')
@click.argument('source_queue', required=True)
@click.argument('destination_queue', required=True)
@click.option('--limit', '-l', 'msglimit', default=None, type=int,
              help='Limit the number of messages')
@click.option('--quiet', '-q', default=False, is_flag=True,
              help='Quiet mode (suppress any output or prompt)')
def move_messages(source_queue, destination_queue, msglimit, quiet):
    """
    Move messages between queues
    """
    resource = get_resource()
    source = SQSQueue.get(resource, source_queue)
    if source.count <= 0 and not quiet:
        click.echo('{} does not have messages available'.format(source.name), err=True)
        return

    destination = SQSQueue.get(resource, destination_queue)
    count = 0
    label = 'Processing messages'
    messages = source.get_messages(limit=msglimit)
    with click.progressbar(messages, label=label, file=_default_text_stderr()) as msgbar:
        for message in msgbar:
            destination.send_message(message.body)
            message.delete()
            count += 1

    if not quiet:
        click.echo('Moved {} message(s) to {}'.format(count, destination.name))


@cli.command('msg-reborn')
@click.argument('source_queue', required=True)
@click.option('--limit', '-l', 'msglimit', default=None, type=int,
              help='Limit the number of messages')
@click.option('--quiet', '-q', default=False, is_flag=True,
              help='Quiet mode (suppress any output or prompt)')
@click.pass_context
def reborn_messages(context, source_queue, msglimit, quiet):
    """
    Move messages from dead-queue to source-queue
    """
    source = SQSQueue.get(get_resource(), source_queue)
    policy = source._aws_queue.attributes.get('RedrivePolicy')
    if policy is None:
        click.echo(
            'Error: the given queue does have a dead-letter-queue configured',
            err=True)
        return

    policy_data = json.loads(policy)
    dq_name = policy_data['deadLetterTargetArn'].split(':')[-1]
    return context.invoke(
        move_messages,
        source_queue=dq_name,
        destination_queue=source.url,
        msglimit=msglimit,
        quiet=quiet,
    )


@cli.command('msg-send')
@click.argument('queue', required=True)
@click.argument('messages', type=click.File('r'), required=False)
@click.option('--quiet', '-q', default=False, is_flag=True,
              help='Quiet mode (suppress any output or prompt)')
@click.pass_context
def send_messages(context, queue, messages, quiet):
    """
    Send messages to queue
    """
    if not messages:
        messages = click.get_text_stream('stdin')

    with messages:
        try:
            message_data = json.load(messages)
        except json.decoder.JSONDecodeError:
            click.echo('read data are not a json, :-(', err=True)
            return

    source = SQSQueue.get(get_resource(), queue)
    for message in message_data['messages']:
        source.send_message(message)

import pika


class MQ:
    def __init__(self, url='localhost', port=5672):
        try:
            # 连接RabbitMQ
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(url, port))
            self.channel = self.connection.channel()
        except Exception as e:
            raise format(e)

    # 声明exchange
    def get_exchange(self, exchange, exchange_type='direct', passive=False, durable=False, auto_delete=False, internal=False, arguments=None):
        self.channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, passive=passive, durable=durable, auto_delete=auto_delete, internal=internal, arguments=arguments)

    # 声明queue
    def get_queue(self, queue, passive=False, durable=False, exclusive=False, auto_delete=False, arguments=None):
        self.channel.queue_declare(queue=queue, passive=passive, durable=durable, exclusive=exclusive, auto_delete=auto_delete, arguments=arguments)

    # 生产者
    def publish(self, exchange, routing_key='', body=None, properties=None, mandatory=False):
        self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body, properties=properties, mandatory=mandatory)

    # 消费者
    def consumer(self, queue, on_message_callback, auto_ack=False, exclusive=False, consumer_tag=None, arguments=None):
        self.channel.basic_consume(queue=queue, on_message_callback=on_message_callback, auto_ack=auto_ack, exclusive=exclusive, consumer_tag=consumer_tag, arguments=arguments)

    # queue与exchange绑定
    def bind(self, queue, exchange, routing_key=None, arguments=None):
        self.channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key, arguments=arguments)

    # 运行消费者
    def start_consumer(self):
        self.channel.start_consuming()


if __name__ == '__main__':
    mq = MQ()
    mq.get_exchange(exchange='test')

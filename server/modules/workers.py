from flask import Blueprint, jsonify, request

from server.model import *
from server.utils import *

workers_module = Blueprint('workers_module', __name__)


def update_worker(worker, worker_data):
    if worker.connection != 'offline':
        worker.connection = 'online'
        worker.save()

    http_request(worker.ip_address, '/update', worker_data)

    for key, val in worker_data.iteritems():
        print(key, val)
        if val:
            setattr(worker, key, val)
    worker.save()
    print('status ', worker.status)


@workers_module.route('/workers/')
def workers():
    workers = {}

    for worker in Workers.select():
        try:
            f = urllib.urlopen('http://' + worker.ip_address)
            worker.connection = 'online'
        except Exception, e:
            print('[Warning] Worker', worker.hostname, 'is not online')
            worker.connection = 'offline'

        workers[worker.hostname] = {"id": worker.id,
                                    "hostname": worker.hostname,
                                    "status": worker.status,
                                    "connection": worker.connection,
                                    "system": worker.system,
                                    "ip_address": worker.ip_address}

    """
    This is a temporary solution for saving the workers connections:
    we read them from the workers dict we just created and build an
    update query for each one of them. It seems not possible to save
    the objects on the fly in the Workers.select() loop above.
    """

    for k, v in workers.iteritems():
        update_query = Workers.update(connection=v['connection']).\
            where(Workers.id == v['id'])
        update_query.execute()

    return jsonify(workers)

@workers_module.route('/workers/update', methods=['POST'])
def workers_update():
    status = request.form['status']
    # TODO parse
    workers_ids = request.form['id']
    workers_list = list_integers_string(workers_ids)
    for worker_id in workers_list:
        print("updating worker %s = %s " % (worker_id, status))
    return "TEMP done updating workers "


@workers_module.route('/workers/edit', methods=['POST'])
def workers_edit():
    worker_ids = request.form['id']
    worker_data = {"status": request.form['status'],
                   "config": request.form['config']}

    if worker_ids:
        for worker_id in list_integers_string(worker_ids):
            worker = Workers.get(Workers.id == worker_id)
            update_worker(worker, worker_data)

        return jsonify(result='success')
    else:
        print('we edit all the workers')
        for worker in Workers.select():
            update_worker(worker, worker_data)

    return jsonify(result='success')


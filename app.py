from flask import Flask, jsonify, make_response, request
import schedule
import time
import logging
import threading 


app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
users_ips = []
users_uuids = []
last_vos = {}
clan_counters = {
    'iorwerth': 0,
    'amlodd': 0,
    'cadarn': 0,
    'crwys': 0,
    'hefin': 0,
    'ithell': 0,
    'meilyr': 0,
    'trahaearn': 0
}

counter_lock = threading.Lock()

def validate_vote(clan1, clan2):
    if last_vos:
        if clan1 in last_vos.values() or clan2 in last_vos.values():
            return False
        else:
            return True
    else: 
        return True 
    

def add_csp_headers(response):
    response.headers.add('Content-Security-Policy', "default-src 'self'; content-src *")
    
    if request.method == 'OPTIONS':
        options_resp = make_response()
        options_resp.headers.add('Access-Control-Allow-Origin', '*')  
        options_resp.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        options_resp.headers.add('Access-Control-Allow-Methods', '*')
        return options_resp
    
    return response

@app.after_request
def apply_csp(response):
    return add_csp_headers(response)


@app.route('/increase_counter', methods=['POST'])
def increase_counter():
    if request.is_json:
        data = request.get_json()
        if 'uuid' in data and data['uuid'] not in users_uuids:
            users_uuids.append(data['uuid']) 
        if 'clans' in data and isinstance(data['clans'], list) and len(data['clans']) == 2:
            valid = validate_vote(data['clans'][0], data['clans'][1])
            if valid == True:
                response = {}
                with counter_lock:
                    for clan in data['clans']:
                        if clan in clan_counters:
                            if clan == data['clans'][0]:
                                clan_counters[clan] += 2
                            else:
                                clan_counters[clan] += 1
                            logging.info(f'SUCCESS, valid vote for {clan} counted. Total count for {clan}: {clan_counters[clan]}')
                            response[clan] = clan_counters[clan]
                        else:
                            response[clan] = 'Not a valid Prifddinas clan.'
            else: 
                response = jsonify({'Error': 'Vote invalid as it voted for a clan in last_vos.'})
                return make_response(response, 400)
            response = jsonify(response)
            return response
        else:
            response = jsonify({'Error': 'Try again'})
            return make_response(response, 400)
    else:
        response = jsonify({'error': 'Invalid JSON'})
        return make_response(response, 400)

@app.route('/vos', methods=['GET'])
def vos():
    with counter_lock:
        requester_ip = request.headers['Fly-Client-Ip']
        if requester_ip not in users_ips:
            users_ips.append(requester_ip)
        sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
        top_2 = [clan[0] for clan in sorted_counts[:2] if clan[1] != 0]
        logging.info(f'Top 2 clans requested')
        response = {f"clan_{index + 1}": clan for index, clan in enumerate(top_2)}
        return make_response(jsonify(response), 200)

@app.route('/counts', methods=['GET'])
def counts():
    with counter_lock:
        sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
        logging.info(f'Counts given.')
        response = {f"count_{index + 1}": {clan[0]: clan[1]} for index, clan in enumerate(sorted_counts)}
        return make_response(jsonify(response), 200)

@app.route('/last_vos', methods=['GET'])
def get_last_vos():
    if last_vos:
        return make_response(jsonify(last_vos), 200)
    else:
        return make_response(jsonify({'message': 'No previous VOS data'}), 404)
        
def reset_counters():
    global last_vos
    with app.app_context():
        with counter_lock:
            logging.info("Unique voters: " + str(len(users_uuids)))
            logging.info("Unique requesters: " + str(len(users_ips)))
            last_vos.clear()
            users_ips.clear()
            users_uuids.clear()
            sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
            top_2 = [clan[0] for clan in sorted_counts[:2] if clan[1] != 0]
            for index, clan in enumerate(top_2):
                last_vos[f"clan_{index + 1}"] = clan
            for clan in clan_counters:
                clan_counters[clan] = 0
    logging.info("Counters reset at " + time.ctime())

def scheduled_task():
    while True:
        now = time.localtime()
        if now.tm_min == 59:
            reset_counters()
            time.sleep(60)
        time.sleep(10) 

scheduler_thread = threading.Thread(target=scheduled_task)
scheduler_thread.start()

if __name__ == '__main__':
    app.run(threaded=True)

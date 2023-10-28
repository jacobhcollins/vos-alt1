from flask import Flask, jsonify, make_response, request
import schedule
import time
import logging
import threading 


app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

ip_addresses_voted  = set()
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
    global ip_addresses_voted
    if request.is_json:
        data = request.get_json()
        client_ip = request.remote_addr
        if client_ip not in ip_addresses_voted:
            if 'clans' in data and isinstance(data['clans'], list) and len(data['clans']) == 2:
                response = {}
                with counter_lock:
                    for clan in data['clans']:
                        if clan in clan_counters:
                            clan_counters[clan] += 1
                            logging.info(f'SUCCESS, {clan} count: {clan_counters[clan]}')
                            response[clan] = clan_counters[clan]
                        else:
                            response[clan] = 'Invalid clan'
                ip_addresses_voted.add(client_ip) 
                response = jsonify(response)
                return response
            else:
                response = jsonify({'error': 'Please provide a list of exactly two clans'})
                return make_response(response, 400)
        else:
            logging.info(f'{client_ip} hit rate limit.')
            response = jsonify({'error': 'Rate limited, try again in an hour.'})
            return make_response(response, 400)
    else:
        response = jsonify({'error': 'Invalid JSON'})
        return make_response(response, 400)

@app.route('/vos', methods=['GET'])
def vos():
    with counter_lock:
        sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
        top_2 = [clan[0] for clan in sorted_counts[:2] if clan[1] != 0]
        logging.info(f'Top 2 clans requested')
        response = {f"clan_{index + 1}": clan for index, clan in enumerate(top_2)}
        return make_response(jsonify(response), 200)

@app.route('/counts', methods=['GET'])
def counts():
    with counter_lock:
        client_ip = request.remote_addr
        sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
        logging.info(f'Counts given to {client_ip}')
        response = {f"count_{index + 1}": {clan[0]: clan[1]} for index, clan in enumerate(sorted_counts)}
        return make_response(jsonify(response), 200)
    
@app.route('/reset', methods=['GET'])   
def reset_counters():
    global ip_addresses_voted 
    ip_addresses_voted = set()
    for clan in clan_counters:
        clan_counters[clan] = 0
    logging.info("Counters and IP logging reset at " + time.ctime())
    return make_response(jsonify({'message': 'Counters and IP logging reset'}), 200)

schedule.every().hour.at(":00").do(reset_counters)

if __name__ == '__main__':
    app.run()
    while True:
        schedule.run_pending()
        time.sleep(5)

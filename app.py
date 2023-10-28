from flask import Flask, jsonify, make_response, request
import schedule
import time
import logging
import threading 


app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

ip_addresses_voted  = []
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
                ip_addresses_voted.append(client_ip)
                response = jsonify(response)
                response.headers.add('Content-Security-Policy', "default-src 'self' *")
                return response
            else:
                response = jsonify({'error': 'Please provide a list of exactly two clans'})
                response.headers.add('Content-Security-Policy', "default-src 'self' *")
                return make_response(response, 400)
        else:
            logging.info(f'{client_ip} hit rate limit.')
            response = jsonify({'error': 'Rate limited, try again in an hour.'})
            response.headers.add('Content-Security-Policy', "default-src 'self' *")
            return make_response(response, 400)
    else:
        response = jsonify({'error': 'Invalid JSON'})
        response.headers.add('Content-Security-Policy', "default-src 'self' *")
        return make_response(response, 400)

@app.route('/vos', methods=['GET'])
def vos():
    with counter_lock:
        sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
        top_2 = [clan[0] for clan in sorted_counts[:2] if clan[1] != 0]
        if len(top_2) == 2:
            return jsonify(top_2)
        else:
            return jsonify(None)

@app.route('/counts', methods=['GET'])
def counts():
    with counter_lock:
        sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
        return jsonify(sorted_counts)
    
@app.route('/reset', methods=['GET'])   
def reset_counters():
    global ip_addresses_voted 
    ip_addresses_voted = []
    for clan in clan_counters:
        clan_counters[clan] = 0
    logging.info("Counters and IP logging reset at " + time.ctime())
    return make_response(jsonify({'Reset app manually'}), 400)

schedule.every().hour.at(":00").do(reset_counters)

if __name__ == '__main__':
    app.run()
    while True:
        schedule.run_pending()
        time.sleep(5)

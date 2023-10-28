from flask import Flask, jsonify, make_response
import schedule
import time
import logging
import threading 

app = Flask(__name__)

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

@app.route('/increase_counter/<clan>', methods=['POST'])
def increase_counter(clan):
    with counter_lock:
        if clan in clan_counters:
            clan_counters[clan] += 1
            return f'SUCCESS, {clan} count: {clan_counters[clan]}'
        else:
            return make_response(jsonify({'error': 'Invalid clan'}), 400)

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
    
def reset_counters():
    for clan in clan_counters:
        clan_counters[clan] = 0
    logging.info("Counters reset at " + time.ctime())

schedule.every().hour.at(":00").do(reset_counters)

if __name__ == '__main__':
    app.run(debug=True)
    while True:
        schedule.run_pending()
        time.sleep(1)

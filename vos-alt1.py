from flask import Flask, jsonify, make_response
import schedule
import time
import logging

app = Flask(__name__)

# Clan counters (stored in memory)
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

# Increase counter for a specific clan
@app.route('/increase_counter/<clan>', methods=['POST'])
def increase_counter(clan):
    if clan in clan_counters:
        clan_counters[clan] += 1
        return f'SUCCESS, {clan} count: {clan_counters[clan]}'
    else:
        return make_response(jsonify({'error': 'Invalid clan'}), 400)

# Get the top 2 counts of the clans
@app.route('/vos', methods=['GET'])
def vos():
    sorted_counts = sorted(clan_counters.items(), key=lambda x: x[1], reverse=True)
    top_2 = [clan[0] for clan in sorted_counts[:2]]  # Extracting only the clan names
    return jsonify(top_2)

# Reset all counters every hour
def reset_counters():
    for clan in clan_counters:
        clan_counters[clan] = 0
    logging.info("Counters reset at " + time.ctime())

# Schedule counter reset every hour
schedule.every().hour.at(":00").do(reset_counters)

# Flask app run
if __name__ == '__main__':
    app.run(debug=True)
    while True:
        schedule.run_pending()
        time.sleep(1)

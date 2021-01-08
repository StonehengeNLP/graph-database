import json
from src import settings
from src import graph_search as gs
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

SWAGGER_URL = '/docs'
API_URL = '/swagger'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ESRA GDBM Swagger"
    },
)
app.register_blueprint(swaggerui_blueprint)

@app.route('/swagger')
def swagger():
    with open('swagger.json') as f:
        swagger_json = json.load(f)
        
    swagger_env = settings.FLASK_ENV
    if swagger_env == 'production':
        swagger_json['host'] = '35.247.162.211'
        swagger_json['schemes'] = ['http']

    return swagger_json
    
@app.route('/complete')
def complete():
    query = request.args.get('q')
    if not query:
        return jsonify({'msg': 'Missing query parameter'}), 400
    
    if len(query.strip()) == 0:
        return {'sentences': []}, 200
    
    tokenized_text = query.split()
    for i in range(len(tokenized_text)):
        temp_text = ' '.join(tokenized_text[i:])
        try:
            out = gs.text_autocomplete(temp_text)
        except:
            return jsonify({'msg': 'Database is not available'}), 503
        if out:
            out = [' '.join(word.split()) for word in out]
            break
    return jsonify({'sentences': out}), 200

@app.route('/preprocess', methods=['POST'])
def preprocess():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400    
    
    text = request.json.get('text')
    if not text:
        return jsonify({"msg": "Missing 'text' parameter"}), 400
    
    try:
        processed_keywords = gs.text_preprocessing(text)
    except:
        return jsonify({'msg': 'Database is not available'}), 503
    return jsonify(processed_keywords), 200

# NOTE: this may be changed from whole paper titles to just their ids
@app.route('/explain', methods=['POST'])
def explanation():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400    
    
    keyword = request.json.get('keyword')
    papers = request.json.get('papers')
    if not keyword:
        return jsonify({"msg": "Missing 'keyword' parameter"}), 400
    if not papers:
        return jsonify({"msg": "Missing 'paperIds' parameter"}), 400
    
    try:
        processed_keywords = gs.text_preprocessing(keyword, flatten=True)
    except Exception as e:
        print(e)
        return jsonify({'msg': 'Database is not available'}), 503
    
    explanations = []
    for paper in papers:
        explanations.append(gs.explain(processed_keywords, paper.lower()))
    return jsonify({'explanations': explanations}), 200

@app.route('/facts')
def list_of_facts():
    query = request.args.get('q')
    if not query:
        return jsonify({'msg': 'Missing query parameter'}), 400
    
    if len(query.strip()) == 0:
        return {'facts': []}, 200
    
    try:
        processed_keywords = gs.text_preprocessing(query, flatten=True)
    except:
        return jsonify({'msg': 'Database is not available'}), 503
    
    fact_list = gs.get_facts(processed_keywords)
    return {'facts': fact_list}, 200

@app.route('/graph')
def graph():
    # keyword = request.args.get('keyword')
    paper_title = request.args.get('paper_title')
    limit = request.args.get('limit', 30, type=int)
    
    # if not keyword:
    #     return jsonify({"msg": "Missing 'keyword' parameter"}), 400
    if not paper_title:
        return jsonify({"msg": "Missing 'paper_title' parameter"}), 400
    
    # try:
    #     processed_keywords = gs.text_preprocessing(keyword, flatten=True)
    # except:
    #     return jsonify({'msg': 'Database is not available'}), 503
    
    graph = gs.query_graph(paper_title=paper_title, limit=limit)
    return {'graph': graph}, 200
    
if __name__ == '__main__':
    app.run(debug=False, port=80, host='0.0.0.0') 

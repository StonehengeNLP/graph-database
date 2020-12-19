import json
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
        'app_name': "Test application"
    },
)
app.register_blueprint(swaggerui_blueprint)

@app.route('/swagger')
def swagger():
    with open('swagger.json') as f:
        swagger_json = json.load(f)
        return swagger_json
    
@app.route('/complete')
def complete():
    query = request.args.get('q')
    if not query:
        return jsonify({'msg': 'Missing query parameter'}), 400
    
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

# NOTE: this may be changed from whole paper titles to just their ids
@app.route('/explain', methods=['POST'])
def explanation():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400    
    
    keyword = request.json.get('keyword', None)
    papers = request.json.get('papers', None)
    if not keyword:
        return jsonify({"msg": "Missing 'keyword' parameter"}), 400
    if not papers:
        return jsonify({"msg": "Missing 'paperIds' parameter"}), 400
    
    processed_keywords = gs.text_preprocessing(keyword)
    explanations = []
    for paper in papers:
        explanations.append(gs.explain(processed_keywords, paper, mode='template'))
    return jsonify({'explanations': explanations}), 200

if __name__ == '__main__':
    app.run(debug=True)
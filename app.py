import os
from flask import Flask
from flask import request
from flask import jsonify
from flask import render_template

from crossref import fetch_links

default_sersol_key = 'rl3tp7zf5x'

app = Flask(__name__)

@app.route('/fetch-cite', methods=['POST'])
def fetch_cite():
    if request.method == 'POST':
        cite = request.form.items()[0][0]
        results = fetch_links(cite)
        return jsonify(results)


@app.route('/resolve/<key>/', methods=['GET'])
@app.route('/resolve/', methods=['GET'])
def resolve(key=None):
    from py360link import get_sersol_data, Resolved
    from py360link.link360 import Link360Exception
    raw_query = request.query_string
    #remove http prefix from doi
    query = raw_query.replace('http://dx.doi.org/', '')
    sersol_key = request.view_args.get('key', default_sersol_key)
    #Setup some defaults for the json response.
    d = {}
    d['key'] = sersol_key
    d['library'] = None 
    d['error'] = False
    d['url'] = None
    d['provider'] = None
    sersol = get_sersol_data(query, key=sersol_key, timeout=10)
    try:
        resolved = Resolved(sersol)
        d['library'] = resolved.library
        groups = resolved.link_groups
        #Get the first link to a full text source
        for grp, link in enumerate(groups):
            article = link['url'].get('article')
            if article:
                d['url'] = article
                d['provider'] = groups[grp]['holdingData']['providerName']
                break
    except Link360Exception:
        d['error'] = True
        print '#ERRROR 360Link %s' % query
    d['query'] = query
    return jsonify(d)


@app.route('/<library>/')
@app.route('/')
def index(library=None):
    ctx = dict(
        ga_tracking_code=os.getenv('GA_TRACKING_CODE'),
        library=library,
    )
    return render_template('index.html', **ctx)


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    params = dict(host='0.0.0.0', port=port)
    if os.environ.get('HOME', '').find('vagrant') > -1:
        params['debug'] = True
    app.run(**params)

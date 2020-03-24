from flask import Flask  # , jsonify, request
from os.path import join, realpath, dirname


class Server(Flask):
    def __init__(self, data_path='data/data.json'):
        Flask.__init__(self, __name__, static_folder='static', static_url_path='')
        self.full_data_path = join(realpath(dirname(__file__)), data_path)
        print(f'serving data from {self.full_data_path}')


app = Server()


@app.route("/")
def index():
    return app.send_static_file('index.html')


@app.route('/api/net')
def get_network():
    print('trying to get network')
    return open(app.full_data_path).read()
    #return app.send_static_file(app.full_data_path)


@app.route('/api/reset')
def reset_network():
    return app.send_static_file(app.full_data_path)


print('**************************************')
print('*       D3 visualisation server      *')
print('*        go to localhost:8000/       *')
print('**************************************')

if __name__ == "__main__":
    app.run(port=8000)

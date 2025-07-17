from app import create_app
from app.views import init_db
import os
import sys

app = create_app()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        with app.app_context():
            print(init_db())
    else:
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', '5000'))
        app.run(host=host, port=port, debug=True)

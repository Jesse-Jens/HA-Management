from app import create_app
from app.views import init_db
import sys

app = create_app()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        with app.app_context():
            print(init_db())
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)

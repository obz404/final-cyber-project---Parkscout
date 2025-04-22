from flask_dashboard.app import app
import flask_dashboard.routes  # make sure routes are loaded

if __name__ == '__main__':
    app.run(debug=True)

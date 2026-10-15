"""Development entry point for the TrackIt application.

``flask --app app run`` and ``python app.py`` are both supported.
"""

from trackit import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

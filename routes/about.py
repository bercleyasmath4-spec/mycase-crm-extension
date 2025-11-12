from flask import Blueprint, render_template

about_bp = Blueprint("about_bp", __name__)

@about_bp.route("/about")
def about():
    """
    Renders the About page for CasePulse AI.
    """
    return render_template("about.html")

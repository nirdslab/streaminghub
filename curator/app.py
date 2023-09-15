from flask import Response, abort, jsonify, redirect, render_template, request, send_file, session
from werkzeug.utils import secure_filename
from urllib.parse import unquote

from config import Config
from util import get_dir_listing, get_filepath, is_hidden, is_media, make_zipfile, send_media, uri_to_dict

config = Config()


@config.app.errorhandler(400)
def err_400(error):
    return render_template("error.html", errorCode=400, errorText="Bad Request"), 400


@config.app.errorhandler(403)
def err_403(error):
    return render_template("error.html", errorCode=200, errorText="Permission Denied"), 403


@config.app.errorhandler(404)
def err_404(error):
    return render_template("error.html", errorCode=404, errorText="Resource Not Found"), 404


@config.app.errorhandler(500)
def err_500(error):
    return render_template("error.html", errorCode=500, errorText="An Internal Error Occured"), 500


@config.app.after_request
def after_request(response: Response) -> Response:
    """ """
    response.headers.add("Accept-Ranges", "bytes")
    return response


@config.app.route("/login/")
@config.app.route("/login/<path:var>")
def loginMethod(var: str = ""):
    if config.pwdHash == "":
        session["login"] = True
    if "login" in session:
        return redirect("/" + var)
    else:
        return render_template("login.html")


@config.app.route("/login/", methods=["POST"])
@config.app.route("/login/<path:var>", methods=["POST"])
def loginPost(var: str = ""):
    text = request.form["text"]
    if text == config.pwdHash:
        session["login"] = True
        return redirect("/" + var)
    else:
        return redirect("/login/" + var)


@config.app.route("/logout/")
def logoutMethod():
    if "login" in session:
        session.pop("login", None)
    return redirect("/login/")


@config.app.route("/changeView")
def changeView():
    v = int(request.args.get("view", 0))
    v = v if v in [0, 1] else 0
    session["view"] = v
    return jsonify(view=v)


def get_view_id():
    view_id = int(session.get("view", config.default_view))
    if view_id not in [0, 1]:
        abort(500)
    return view_id


def ensure_logged_in(redirect_path: str):
    if "login" not in session:
        return redirect(redirect_path)


@config.app.route("/files/", methods=["GET", "POST"])
@config.app.route("/files/<path:var>", methods=["GET", "POST"])
def filePage(var: str = ""):
    path = get_filepath(var, config)
    ensure_logged_in("/login/files/" + var)
    if not path.exists():
        abort(404)
    if not path.is_dir():
        abort(400)
    try:
        dir_dict, file_dict = get_dir_listing(path, config)
        view_id = get_view_id()
    except:
        abort(500)

    parts = var.strip("/").split("/")
    path_html = '<a href="/files"><img src="/static/root.png" style="height:25px;width:25px;">&nbsp;</a>'
    for c in range(len(parts)):
        p_url = "/".join(parts[0 : c + 1])
        p_name = unquote(parts[c])
        path_html += f' / <a style="color:black;" href="/files/{p_url}">{p_name}</a>'
    logged_in = "login" in session

    # if method is POST
    config.app.logger.info(f"method={request.method}")
    if request.method == "POST":
        action = request.form.get("action")
        assert action is not None
        if action == "update":
            paths = request.form.getlist("selection[]")
            patch = {k: uri_to_dict(k, config) for k in paths}
            if "selection" in session:
                state = dict(session["selection"])
                state.update(patch)
                session["selection"] = state
            else:
                session["selection"] = patch
            config.app.logger.info(f"updated selection: {len(patch)} selected")
        if action == "reset":
            session["selection"] = {}
        return redirect("/files/" + var)
    return render_template(
        "home.html",
        selection_dict=dict(session.get("selection", {})),
        dir_dict=dir_dict,
        file_dict=file_dict,
        view_id=view_id,
        breadcrumbs=path_html,
        logged_in=logged_in,
    )


@config.app.route("/", methods=["GET"])
def homePage():
    return redirect("/files")


@config.app.route("/browse/<path:var>", defaults={"browse": True})
@config.app.route("/download/<path:var>", defaults={"browse": False})
def browseFile(var: str, browse: bool):
    if "login" not in session:
        return redirect("/login/download/" + var)
    path = get_filepath(var, config)
    try:
        if not browse:
            return send_file(path, download_name=path.name)
        flag, tp, ext = is_media(path, config)
        if flag:
            return send_media(path, f"{tp}/{ext}")
        return send_file(path)
    except:
        abort(404)


@config.app.route("/downloadFolder/<path:var>")
def downloadFolder(var: str):
    if "login" not in session:
        return redirect("/login/downloadFolder/" + var)
    path = get_filepath(var, config)
    assert path.is_dir()
    if is_hidden(path, config):
        abort(403)
    zip_name = path.with_suffix(".zip").name
    zip_path = config.temp_dir / zip_name
    try:
        make_zipfile(zip_path, path)
        return send_file(zip_path, download_name=zip_name)
    except:
        abort(500)


@config.app.route("/upload/", methods=["POST"])
@config.app.route("/upload/<path:var>", methods=["POST"])
def uploadFile(var: str = ""):
    if "login" not in session:
        return render_template("login.html")
    text = ""
    path = get_filepath(var, config)
    assert path.is_dir()
    if is_hidden(path, config):
        abort(403)
    files = request.files.getlist("files[]")
    num_total = len(files)
    num_failed = 0
    for file in files:
        assert file.filename
        filename = secure_filename(file.filename)
        fupload = path / filename
        if not fupload.exists():
            try:
                file.save(fupload)
                config.app.logger.info(filename + " Uploaded")
                text = text + filename + " Uploaded<br>"
            except Exception as e:
                num_failed += 1
                config.app.logger.info(filename + " Failed with Exception " + str(e))
                text = text + filename + " Failed with Exception " + str(e) + "<br>"
                continue
        else:
            config.app.logger.info(filename + " Failed because File Already Exists or File Type Issue")
            text = text + filename + " Failed because File Already Exists or File Type not secure <br>"
    return render_template("uploadsuccess.html", text=text, fileNo=num_total, fileNo2=num_failed)


if __name__ == "__main__":
    local = "127.0.0.1"
    public = "0.0.0.0"
    config.app.run(host=public, debug=True, port=8000)

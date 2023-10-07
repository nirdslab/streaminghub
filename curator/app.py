from pathlib import Path
from flask import Response, abort, jsonify, redirect, render_template, request, send_file, session
from werkzeug.utils import secure_filename
from urllib.parse import unquote

from config import Config
import util

config = Config()


def rereference_selection(new_base: Path):
    prefix = Path()
    if new_base.is_relative_to(config.base_dir):
        new_base = new_base.relative_to(config.base_dir)
    else:
        prefix  = config.base_dir.relative_to(new_base)
    tgt = {}
    if "selection" in session:
        for k, v in session["selection"].items():
            pk = Path(k)
            if pk.is_relative_to(new_base):
                rp = pk.relative_to(new_base)
            else:
                rp = prefix / pk
            rk = rp.as_posix()
            rv = util.uri_to_dict(rk, config, new_base)
            rv["metadata"] = dict(v["metadata"])
            tgt[rk] = rv
    session["selection"] = tgt


@config.app.errorhandler(400)
def err_400(error):
    return render_template("error.html", errorCode=400, errorText="Your made an invalid request."), 400


@config.app.errorhandler(403)
def err_403(error):
    return render_template("error.html", errorCode=403, errorText="The requested resource is forbidden."), 403


@config.app.errorhandler(404)
def err_404(error):
    return render_template("error.html", errorCode=404, errorText="The requested resource does not exist."), 404


@config.app.errorhandler(500)
def err_500(error):
    return render_template("error.html", errorCode=500, errorText="We ran into an internal problem"), 500


@config.app.after_request
def after_request(response: Response) -> Response:
    """ """
    response.headers.add("Accept-Ranges", "bytes")
    return response


@config.app.route("/login/")
@config.app.route("/login/<path:var>")
def loginMethod(var: str = ""):
    if config.pwd_hash == "":
        session["login"] = True
    if "login" in session:
        return redirect("/" + var)
    else:
        return render_template("login.html")


@config.app.route("/login/", methods=["POST"])
@config.app.route("/login/<path:var>", methods=["POST"])
def loginPost(var: str = ""):
    text = request.form["text"]
    if text == config.pwd_hash:
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
    path = util.get_filepath(var, config.base_dir)
    ensure_logged_in("/login/files/" + var)
    if not path.exists():
        abort(404)
    if not path.is_dir():
        abort(400)
    try:
        dir_dict, file_dict = util.get_dir_listing(path, config)
        view_id = get_view_id()
    except:
        abort(500)

    parts = var.strip("/").split("/")
    path_html = '<a class="text-link" href="/files"><img class="icon" src="/static/root.png"></a>'
    for c in range(len(parts)):
        p_url = "/".join(parts[0 : c + 1])
        p_name = unquote(parts[c])
        path_html += f'<span class="mx-1">/</span><a class="text-link" href="/files/{p_url}">{p_name}</a>'
    logged_in = "login" in session

    dataset_name = session.get("dataset_name", "")

    # if method is POST
    config.app.logger.info(f"method={request.method}")
    if request.method == "POST":
        action = request.form.get("action")
        assert action is not None

        # update selection
        if action == "update":
            paths = request.form.getlist("selection[]")
            patch = {k: util.uri_to_dict(k, config) for k in paths}
            if "selection" in session:
                selection = dict(session["selection"])
                selection.update(patch)
                session["selection"] = selection
            else:
                session["selection"] = patch
            config.app.logger.info(f"updated selection: {len(paths)} added")

        # drop items from selection
        if action == "drop":
            paths = request.form.getlist("selection[]")
            if "selection" in session:
                selection = dict(session["selection"])
                for p in paths:
                    selection.pop(p, None)
                session["selection"] = selection
            else:
                abort(500)
            config.app.logger.info(f"updated selection: {len(paths)} dropped")

        # clear metadata from selection
        if action == "clear":
            paths = request.form.getlist("selection[]")
            if "selection" in session:
                selection = dict(session["selection"])
                for p in paths:
                    selection[p]["metadata"].clear()
                session["selection"] = selection
            else:
                abort(500)
            config.app.logger.info(f"updated selection: {len(paths)} dropped")

        # reset selection
        if action == "reset":
            session["selection"] = {}

        # run pattern on file name or path name
        if action in ["name_pattern", "path_pattern"]:
            assert "selection" in session
            selection = dict(session["selection"])
            pattern = request.form.get(action)
            assert pattern is not None
            paths = request.form.getlist("selection[]")
            for k in paths:
                assert k in selection
                uri_dict = selection[k]
                assert type(uri_dict["metadata"]) == dict
                patch = util.run_pattern(k, pattern, action, config)
                uri_dict["metadata"].update(patch)
            session["selection"] = selection

        # run dataset naming
        if action == "dataset_name":
            name = request.form.get("dataset_name")
            session["dataset_name"] = name

        if action.startswith("drop_single"):
            name = action[11:]
            selection = session["selection"]
            assert type(selection) == dict
            selection.pop(name, None)

        if action == "reset_root":
            if config.base_dir != config.orig_base_dir:
                rereference_selection(config.orig_base_dir)
                rp = config.base_dir.relative_to(config.orig_base_dir)
                config.base_dir = config.orig_base_dir
                return redirect(f"/files/" + rp.as_posix())

        if action == "set_root":
            rereference_selection(path)
            config.base_dir = path
            return redirect("/files")

        # redirection
        return redirect("/files/" + var)

    return render_template(
        "home.html",
        dataset_name=dataset_name,
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
    path = util.get_filepath(var, config.base_dir)
    try:
        if not browse:
            return send_file(path, download_name=path.name)
        flag, tp, ext = util.is_media(path, config)
        if flag:
            return util.send_media(path, f"{tp}/{ext}")
        return send_file(path)
    except:
        abort(500)


@config.app.route("/download_dir/<path:var>")
def download_folder(var: str):
    if "login" not in session:
        return redirect("/login/downloadFolder/" + var)
    path = util.get_filepath(var, config.base_dir)
    assert path.is_dir()
    if util.is_hidden(path, config):
        abort(403)
    zip_name = path.with_suffix(".zip").name
    zip_path = config.temp_dir / zip_name
    try:
        util.zip_directory(zip_path, path)
        return send_file(zip_path, download_name=zip_name)
    except:
        abort(500)


@config.app.route("/upload/", methods=["POST"])
@config.app.route("/upload/<path:var>", methods=["POST"])
def upload_file(var: str = ""):
    if "login" not in session:
        return render_template("login.html")
    text = ""
    path = util.get_filepath(var, config.base_dir)
    assert path.is_dir()
    if util.is_hidden(path, config):
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


@config.app.route("/metadata", methods=["GET"])
def get_metadata():
    files = request.args.getlist("files[]")
    state = dict(session["selection"])
    metadata = {}
    for file in files:
        if file not in state:
            abort(400)
        metadata[file] = state[file]["metadata"]
    return metadata


if __name__ == "__main__":
    local = "127.0.0.1"
    public = "0.0.0.0"
    config.app.run(host=public, debug=True, port=8000)

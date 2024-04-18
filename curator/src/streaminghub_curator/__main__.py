import argparse
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

from flask import Response, abort, jsonify, redirect, render_template, request, send_file, session
from streaminghub_curator.typing import FileDescriptor
from streaminghub_pydfds.readers import create_reader
from werkzeug.utils import secure_filename

from . import util
from .config import Config

config = Config()

field_spec = dict(
    id="",
    name="",
    description="",
    dtype="f32",
)
stream_spec = dict(
    id="",
    name="",
    description="",
    unit="",
    frequency=0,
    fields=[field_spec.copy()],
    index=[field_spec.copy()],
)
default_spec = [stream_spec.copy()]


def get_selection() -> dict[str, FileDescriptor]:
    if "selection" in session:
        return session["selection"]
    else:
        return {}


def set_selection(selection):
    session["selection"] = selection


def rereference_selection(prev_base: Path, new_base: Path):
    rel_base = new_base
    prefix = Path()
    if rel_base.is_relative_to(prev_base):
        rel_base = rel_base.relative_to(prev_base)
    else:
        prefix = prev_base.relative_to(rel_base)
    tgt: dict[str, FileDescriptor] = {}
    for k, v in get_selection().items():
        pk = Path(k)
        if pk.is_relative_to(rel_base):
            rp = pk.relative_to(rel_base)
        else:
            rp = prefix / pk
        rk = rp.as_posix()
        rv = util.uri_to_dict(rk, rel_base, config.ext_dict)
        rv.metadata = v.metadata
        tgt[rk] = rv
    return tgt


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
    base_dir = Path(session.get("base_dir", config.base_dir))
    path = util.get_filepath(var, base_dir)
    ensure_logged_in("/login/files/" + var)
    if not path.exists():
        abort(404)
    if not path.is_dir():
        abort(400)
    try:
        dir_dict, file_dict = util.get_dir_listing(path, base_dir, config.ext_dict, config.hidden_list)
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
            patch = {k: util.uri_to_dict(k, base_dir, config.ext_dict) for k in paths}
            selection = get_selection()
            selection.update(patch)
            set_selection(selection)
            config.app.logger.info(f"updated selection: {len(paths)} added")

        # drop items from selection
        if action == "drop":
            paths = request.form.getlist("selection[]")
            selection = get_selection()
            for p in paths:
                selection.pop(p, None)
            set_selection(selection)
            config.app.logger.info(f"updated selection: {len(paths)} dropped")

        # clear metadata from selection
        if action == "clear":
            paths = request.form.getlist("selection[]")
            selection = get_selection()
            for p in paths:
                selection[p].metadata.clear()
            set_selection(selection)
            config.app.logger.info(f"updated selection: {len(paths)} dropped")

        # reset selection
        if action == "reset":
            set_selection({})

        # run pattern on file name or path name
        if action in ["name_pattern", "path_pattern"]:
            selection = get_selection()
            pattern = request.form.get(action)
            assert pattern is not None
            paths = request.form.getlist("selection[]")
            for k in paths:
                assert k in selection
                uri_dict = selection[k]
                patch = util.run_pattern(k, pattern, action, base_dir)
                uri_dict.metadata.update(patch)
            set_selection(selection)

        # run dataset naming
        if action == "dataset_name":
            name = request.form.get("dataset_name")
            session["dataset_name"] = name

        if action.startswith("drop_single"):
            name = action[11:]
            selection = get_selection()
            assert type(selection) == dict
            selection.pop(name, None)

        if action == "reset_root":
            if base_dir != config.base_dir:
                tgt = rereference_selection(base_dir, config.base_dir)
                set_selection(tgt)
                session.pop("base_dir")
                rp = base_dir.relative_to(config.base_dir)
                return redirect(f"/files/" + rp.as_posix())

        if action == "set_root":
            tgt = rereference_selection(base_dir, path)
            set_selection(tgt)
            session["base_dir"] = path.as_posix()
            return redirect("/files")

        # redirection
        return redirect("/files/" + var)

    return render_template(
        "home.html",
        dataset_name=dataset_name,
        selection_dict=get_selection(),
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
    base_dir = session.get("base_dir", config.base_dir)
    if "login" not in session:
        return redirect("/login/download/" + var)
    path = util.get_filepath(var, base_dir)
    try:
        if not browse:
            return send_file(path, download_name=path.name)
        flag, tp, ext = util.is_media(path, config.ext_dict)
        if flag:
            return util.send_media(path, f"{tp}/{ext}")
        return send_file(path)
    except:
        abort(500)


@config.app.route("/download_dir/<path:var>")
def download_folder(var: str):
    base_dir = session.get("base_dir", config.base_dir)
    if "login" not in session:
        return redirect("/login/downloadFolder/" + var)
    path = util.get_filepath(var, base_dir)
    assert path.is_dir()
    if util.is_hidden(path, config.hidden_list):
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
    base_dir = session.get("base_dir", config.base_dir)
    if "login" not in session:
        return render_template("login.html")
    text = ""
    path = util.get_filepath(var, base_dir)
    assert path.is_dir()
    if util.is_hidden(path, config.hidden_list):
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


@config.app.route("/streams", methods=["GET"])
def get_streams():
    selection = get_selection()
    uniques = util.find_unique_attributes(selection)
    pattern = list(uniques.keys())
    return render_template("streams.html", file_dict=selection, pattern=pattern, location="")


@config.app.route("/export", methods=["GET"])
def get_export():
    selection = get_selection()
    uniques = util.find_unique_attributes(selection)
    pattern = list(uniques.keys())
    return render_template("export.html", file_dict=selection, pattern=pattern, location="")


@config.app.route("/export", methods=["POST"])
def do_export():
    format = str(request.form.get("format"))
    pattern: list[str] = request.form.getlist("pattern[]")
    config.app.logger.info(f"pattern={pattern}, format={format}")
    assert format in ["h5", "csv", "parquet", "npy"]
    assert len(pattern) > 0

    # TODO create dataset in temp/ folder and push it as a download.
    selection = get_selection()
    for file in selection:
        config.app.logger.info(file)
    return render_template("export.html", file_dict=selection, pattern=pattern)


@config.app.route("/streamspec", methods=["POST"])
def update_stream_spec():
    spec = request.get_json()
    config.app.logger.info(f"spec={spec}")
    session["spec"] = spec
    return jsonify(dict(success=True, error=None))


@config.app.route("/attributes", methods=["GET"])
def get_attribute_editor():
    return render_template("attributes.html")


@config.app.route("/attribmap", methods=["POST"])
def set_attribute_editor():
    mapping = request.get_json()
    config.app.logger.info(f"mapping={mapping}")
    session["mapping"] = mapping
    return jsonify(dict(success=True, error=None))


@config.app.route("/attribmap", methods=["GET"])
def get_attribute_map():
    # forward index
    # { path, ref } -> { {col, dtype}, meta }
    fwd_index: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    base_dir = Path(session.get("base_dir", config.base_dir))
    for path, desc in get_selection().items():
        cols = create_reader(base_dir / path).lsfields()
        meta = desc.metadata
        # broadcast metadata to all entries in the fields dict
        for ref, colmap in cols.items():
            fwd_index[(path, ref)] = dict(cols=colmap, meta=meta)

    # inverse index
    # {col} -> [ {path, ref, dtype, meta} ]
    inv_index: defaultdict[str, list[dict[str, str | dict[str, str]]]] = defaultdict(list)
    for (path, ref), entries in fwd_index.items():
        cols, meta = entries["cols"], entries["meta"]
        for col, dtype in cols.items():
            inv_index[col].append(
                dict(
                    path=path,
                    ref=ref,
                    dtype=dtype,
                    meta=meta,
                )
            )

    # number of units in selection
    file_count = len(fwd_index)
    cols_count = {str(k): len(v) for k, v in inv_index.items()}
    # get max occurence count of the attributes
    max_count = max(cols_count.values())
    # ensure at least one column is common across all files
    assert max_count == file_count
    final_index = {
        k: {
            "items": v,
            "summary": {
                "count": len(v),
                # bool indicating if attribute has full coverage
                "fully_covered": len(v) == max_count,
            },
        }
        for k, v in inv_index.items()
    }
    return jsonify(dict(cols=final_index, file_count=file_count, mapping=session.get("mapping", None)))


@config.app.route("/streamspec", methods=["GET"])
def get_stream_spec():
    spec = session.get("spec", default_spec)
    return jsonify(spec)


@config.app.route("/metadata", methods=["POST"])
def get_metadata():
    files = request.get_json()["files"]
    selection = get_selection()
    metadata = {}
    for file in files:
        if file not in selection:
            abort(400)
        metadata[file] = selection[file].metadata
    return metadata


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Streaminghub Curator")
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0")
    parser.add_argument("--port", "-p", type=int, default=8000)
    args = parser.parse_args()

    config.app.run(host=args.host, port=args.port, debug=True)

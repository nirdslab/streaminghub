const MetadataEditor = ({ meta }) => {
    console.log(meta);
    const [count, setCount] = React.useState(0);
    const tags = {};
    const empty = [];
    Object.entries(meta).forEach(([f, kv]) => {
        if (Object.keys(kv).length == 0) {
            empty.push(f);
        } else {
            Object.entries(kv).forEach(([k, v]) => {
                if (!(k in tags)) {
                    tags[k] = {}
                }
                if (v in tags[k]) {
                    tags[k][v].push([f])
                } else {
                    tags[k][v] = [f]
                }
            });
        }
    });
    console.log(tags);

    const pills = (f) => {
        const arr = Array.from(f);
        if (arr.length == 0) {
            return (<div className="text-center m-2">No Items</div>)
        } else {
            return arr.map(fi => (
                <li type="button" className="btn btn-sm m-1 px-1 py-0 btn-outline-success">{fi}</li>
            ));
        }
    }

    const group = (vf) => Object.entries(vf).map(([v, f]) => (
        <li className="list-group-item"><b>{v}</b><ul>{pills(f)}</ul></li>
    ))


    const htmlTags = Object.entries(tags).map(([k, vf]) => (
        <div className="col-6 my-2">
            <div className="card">
                <div className="card-header bg-success text-light py-1 text-center"><b>{k}</b></div>
                <ul className="list-group list-group-flush">{group(vf)}</ul>
            </div>
        </div>
    ))

    return (
        <>
            <div className="row d-flex">{htmlTags}</div>
            <div className="row">
                <div className="col my-2">
                    <div className="card">
                        <div className="card-header bg-warning py-1 text-center"><b>Not Annotated</b></div>
                        <ul className="list-group list-group-flush">{pills(empty)}</ul>
                    </div>
                </div>
            </div>
        </>);
};
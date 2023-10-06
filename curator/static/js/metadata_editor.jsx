const MetadataEditor = ({ tags }) => {
    const [count, setCount] = React.useState(0);

    const htmlTags = Object.entries(tags).map(([k, v]) => (
        <button type="button" name="" class="btn btn-sm px-1 py-0 btn-success">{k}: <b>{v}</b></button>
    ))

    return (
        <>
            <div>
                Hello without NPM {count}
            </div>
            <div class="row ms-3 mt-1">
                <div class="col-12 ms-3">
                    {htmlTags}
                    <button className="btn btn-sm px-1 py-0 btn-primary" type="button" onClick={() => setCount(count + 1)}>Add</button>
                </div>
            </div>
        </>
    );
};
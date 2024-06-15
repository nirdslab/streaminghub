function AttributeMapper({ streams, attributeMap, saveAttributeMap }) {
  // get/create default mapping
  const defaultMapping =
    attributeMap.mapping ||
    streams.reduce((m, stream) => {
      m[stream.id] = {};
      stream.fields.forEach((rec) => (m[stream.id][rec.id] = ""));
      stream.index.forEach((rec) => (m[stream.id][rec.id] = ""));
      return m;
    }, {});
  const [mapping, setMapping] = React.useState(defaultMapping);

  // update internal state
  const updateMapping = (streamId, recId, attrId) => {
    const newMapping = { ...mapping };
    newMapping[streamId][recId] = attrId;
    setMapping(newMapping);
  };

  const saveMapping = () => {
    const cleanMapping = streams.reduce((m, stream) => {
      const mi = {};
      stream.fields.forEach((f) => (mi[f.id] = mapping[stream.id][f.id]));
      stream.index.forEach((f) => (mi[f.id] = mapping[stream.id][f.id]));
      m[stream.id] = mi;
      return m;
    }, {});
    saveAttributeMap(cleanMapping);
  };

  return (
    <>
      <div className="row">
        <div className="col">
          <p>
            We processed each file and extracted their attributes (e.g., column names) for you. Use the section below to
            map each field you've specified in your streams to an attribute.
          </p>
        </div>
      </div>
      <div className="row">
        <div className="col mb-2">
          <button className="btn btn-sm btn-success me-1" onClick={(e) => saveMapping(mapping)}>
            <i className="fa fa-save me-1"></i>Save Mapping
          </button>
        </div>
      </div>
      <div>
        {streams.map((stream) => (
          <StreamAttributeMapper
            key={stream.id}
            stream={stream}
            attrs={attributeMap}
            mapping={mapping[stream.id]}
            updateMapping={(key, val) => updateMapping(stream.id, key, val)}
          ></StreamAttributeMapper>
        ))}
      </div>
    </>
  );
}

function StreamAttributeMapper({ stream, attrs, mapping, updateMapping }) {
  const renderRecord = (ref, idx, record) => (
    <div className="row" key={`${ref}_${idx}`}>
      <div className="input-group">
        <div className="col-4">
          <label className="input-group-text bg-dark text-light">
            <div className="fw-bold">{record.id}</div>
            <div className="d-flex ms-auto">
              ({record.name}) ({record.dtype})
            </div>
          </label>
        </div>
        <div className="col-8">
          <select
            type="text"
            className="form-control form-control-sm"
            value={mapping[record.id]}
            onChange={(e) => updateMapping(record.id, e.target.value)}
          >
            <option key="" value="">
              (Not Selected)
            </option>
            {Object.entries(attrs.cols).map(([k, v], idx) => (
              <option key={idx} value={k} disabled={!v.summary.fully_covered}>
                {k} {v.summary.fully_covered ? "" : `(only in ${v.summary.count}/${attrs.file_count} files)`}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );

  return (
    <div className="card my-1 border-2 border-secondary">
      <div className="card-header border-2 border-secondary p-0">
        <div className="input-group">
          <label className="input-group-text bg-secondary text-light border-0 " style={{ borderRadius: 0 }}>
            <b className="px-2">{stream.id}</b>({stream.name})
          </label>
          <div className="d-flex ms-auto">
            <label className="input-group-text">unit = {stream.unit}</label>
            <label className="input-group-text">frequency = {stream.frequency} Hz</label>
          </div>
        </div>
      </div>
      <div className="card-body py-0 px-1">
        <div className="row pt-1">
          <div className="col">
            <div className="card">
              <div className="card-header d-flex flex-row p-0 ps-3">
                <div className="d-flex align-items-center">
                  <span>
                    <b className="me-2">Fields</b>({stream.fields.length})
                  </span>
                </div>
              </div>
              <div className="card-body p-1">
                {stream.fields.map((record, idx) => renderRecord("fields", idx, record))}
              </div>
            </div>
          </div>
        </div>
        <div className="row pt-1 pb-1">
          <div className="col">
            <div className="card">
              <div className="card-header d-flex flex-row p-0 ps-3">
                <div className="d-flex align-items-center">
                  <span>
                    <b className="me-2">Index</b>({stream.index.length})
                  </span>
                </div>
              </div>
              <div className="card-body p-1">
                {stream.index.map((record, idx) => renderRecord("index", idx, record))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

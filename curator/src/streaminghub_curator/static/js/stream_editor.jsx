function StreamEditor({ spec, saveState }) {
  const fieldSpec = {
    id: "",
    name: "",
    description: "",
    dtype: "f32",
  };
  const template = {
    id: "",
    name: "",
    description: "",
    unit: "",
    frequency: 0,
    fields: [{ ...fieldSpec }],
    index: [{ ...fieldSpec }],
  };
  const [streams, setStreams] = React.useState(spec);

  const addNewStream = () => {
    const newStreams = [...streams];
    newStreams.push({ ...template });
    setStreams(newStreams);
  };

  const saveStreams = () => {
    return saveState(streams).then(() => location.reload());
  };

  const resetStreams = () => {
    const newStreams = [{ ...template }];
    return saveState(newStreams).then(() => location.reload());
  };

  const setStream = (stream, idx) => {
    const newStreams = [...streams];
    newStreams[idx] = stream;
    setStreams(newStreams);
  };

  const dropStream = (idx) => {
    const newStreams = streams.filter((_, i) => i !== idx);
    setStreams(newStreams);
  };

  return (
    <>
      <div className="row">
        <div className="col">
          <p>Use the section below to specify which streams you wish to generate from the chosen data.</p>
        </div>
      </div>
      <div className="row">
        <div className="col mb-2">
          <button className="btn btn-sm btn-primary me-1" onClick={addNewStream}>
            Add Stream
          </button>
          <button className="btn btn-sm btn-success me-1" onClick={saveStreams}>
            <i className="fa fa-save me-1"></i>Save Streams
          </button>
          <button className="btn btn-sm btn-warning me-1" onClick={resetStreams}>
            <i className="fa fa-undo me-2" aria-hidden="true"></i>Reset
          </button>
        </div>
      </div>
      <div className="tall-container">
        {streams.map((stream, idx) => (
          <StreamEntryEditor
            key={idx}
            stream={stream}
            setStream={(s) => setStream(s, idx)}
            dropStream={() => dropStream(idx)}
            fieldSpec={fieldSpec}
          ></StreamEntryEditor>
        ))}
      </div>
    </>
  );
}

function StreamEntryEditor({ stream, setStream, dropStream, fieldSpec }) {
  const updateRecord = (ref, key, field, value) => {
    const newStream = { ...stream };
    newStream[ref][key][field] = value;
    setStream(newStream);
  };
  const addRecord = (ref) => {
    const newStream = { ...stream };
    newStream[ref].push({ ...fieldSpec });
    setStream(newStream);
  };
  const dropRecord = (ref, key) => {
    const newStream = { ...stream };
    newStream[ref] = newStream[ref].filter((_, i) => i !== key);
    setStream(newStream);
  };

  const renderRecord = (ref, idx, record) => (
    <div className="row" key={`${ref}_${idx}`}>
      <div className="col">
        <div className="input-group">
          <label className="input-group-text">ID</label>
          <input
            type="text"
            className="form-control form-control-sm"
            value={record.id}
            onChange={(e) => updateRecord(ref, idx, "id", e.target.value)}
          />
          <label className="input-group-text">Name</label>
          <input
            type="text"
            className="form-control form-control-sm"
            value={record.name}
            onChange={(e) => updateRecord(ref, idx, "name", e.target.value)}
          />
          <label className="input-group-text">Description</label>
          <input
            type="text"
            className="form-control form-control-sm"
            value={record.description}
            onChange={(e) => updateRecord(ref, idx, "description", e.target.value)}
          />
          <label className="input-group-text">Type</label>
          <select
            type="text"
            className="form-control form-control-sm"
            value={record.dtype}
            onChange={(e) => updateRecord(ref, idx, "dtype", e.target.value)}
          >
            <option value="f16">float16</option>
            <option value="f32">float32</option>
            <option value="f64">float64</option>
            <option value="i8">int8</option>
            <option value="i16">int16</option>
            <option value="i32">int32</option>
            <option value="u8">uint8</option>
            <option value="u16">uint16</option>
            <option value="u32">uint32</option>
            <option value="byte">byte</option>
          </select>
          <button className="btn btn-sm btn-outline-secondary p-0" onClick={(e) => dropRecord(ref, idx)}>
            <i className="fas fa-trash p-2"></i>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="card my-1 border-2 border-secondary">
      <div className="card-header border-2 border-secondary p-0">
        <div className="input-group">
          <label className="input-group-text bg-secondary border-0" style={{"borderRadius": 0}}>
            <b className="px-2 text-light">ID</b>
          </label>
          <input
            type="text"
            className="form-control form-control-sm"
            placeholder="Stream ID"
            value={stream.id}
            onChange={(e) => setStream({ ...stream, id: e.target.value })}
          />
          <button className="btn btn-secondary p-0" onClick={dropStream} style={{"borderRadius": 0}}>
            <i className="fas fa-trash p-2"></i>
          </button>
        </div>
      </div>
      <div className="card-body py-0 px-1">
        <div className="row pt-1">
          <div className="col">
            <div className="card">
              <div className="card-header d-flex flex-row p-1 ps-3">
                <div className="d-flex align-items-center">
                  <span><b className="me-2">Details</b></span>
                </div>
              </div>
              <div className="card-body p-1">
                <div className="row">
                  <div className="col">
                    <div className="input-group">
                      <label className="input-group-text">Name</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        value={stream.name}
                        onChange={(e) => setStream({ ...stream, name: e.target.value })}
                      />
                      <label className="input-group-text">Description</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        value={stream.description}
                        onChange={(e) => setStream({ ...stream, description: e.target.value })}
                      />
                      <label className="input-group-text">Unit</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        value={stream.unit}
                        onChange={(e) => setStream({ ...stream, unit: e.target.value })}
                      />
                      <label className="input-group-text">Frequency (Hz)</label>
                      <input
                        type="number"
                        className="form-control form-control-sm"
                        value={stream.frequency}
                        onChange={(e) => setStream({ ...stream, frequency: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="row pt-1">
          <div className="col">
            <div className="card">
              <div className="card-header d-flex flex-row p-0 ps-3">
                <div className="d-flex align-items-center">
                  <span>
                    <b className="me-2">Fields</b>({stream.fields.length})
                  </span>
                </div>
                <div className="d-flex ms-auto me-1">
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary p-0"
                    onClick={() => addRecord("fields")}
                  >
                    <i className="fa-solid fa-plus p-2"></i>
                  </button>
                </div>
              </div>
              <div className="card-body p-1">{stream.fields.map((record, idx) => renderRecord("fields", idx, record))}</div>
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
                <div className="d-flex ms-auto me-1">
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary p-0"
                    onClick={() => addRecord("index")}
                  >
                    <i className="fa-solid fa-plus p-2"></i>
                  </button>
                </div>
              </div>
              <div className="card-body p-1">{stream.index.map((record, idx) => renderRecord("index", idx, record))}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
